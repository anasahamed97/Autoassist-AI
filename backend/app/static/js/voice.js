/**
 * AutoAssist AI - Complete Multilingual Voice Input (STT) & Voice Output (TTS) Engine
 * Supported Languages:
 *   - English (en-IN / en-US)
 *   - Kannada (kn-IN — ಕನ್ನಡ)
 *   - Hindi (hi-IN — हिन्दी)
 *   - Urdu (ur-IN — اردو, RTL)
 *   - Malayalam (ml-IN — മലയാളം)
 *   - Tamil (ta-IN — தமிழ்)
 *   - Telugu (te-IN — తెలుగు)
 *
 * Guarantees:
 *   1. Real-time transcription into the target input box as words are spoken
 *   2. Dual-engine STT: Native Web Speech API + 16kHz PCM WAV Google STT Fallback
 *   3. Never outputs placeholder strings like "Audio successfully captured" into the text box
 *   4. High-fidelity Server-side MP3 Blob Audio Player via POST /api/voice/synthesize
 */

class PcmWavRecorder {
  constructor() {
    this.audioContext = null;
    this.mediaStream = null;
    this.processor = null;
    this.input = null;
    this.pcmChunks = [];
    this.sampleRate = 16000;
  }

  async start() {
    this.pcmChunks = [];
    this.mediaStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        channelCount: 1,
        sampleRate: 16000,
        echoCancellation: true,
        noiseSuppression: true,
      },
    });

    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    this.audioContext = new AudioContextClass({ sampleRate: 16000 });
    this.sampleRate = this.audioContext.sampleRate || 16000;

    this.input = this.audioContext.createMediaStreamSource(this.mediaStream);
    // 4096 buffer size, 1 input channel, 1 output channel
    this.processor = this.audioContext.createScriptProcessor(4096, 1, 1);

    this.processor.onaudioprocess = (e) => {
      const channelData = e.inputBuffer.getChannelData(0);
      this.pcmChunks.push(new Float32Array(channelData));
    };

    this.input.connect(this.processor);
    this.processor.connect(this.audioContext.destination);
  }

  async stop() {
    if (this.processor && this.input) {
      try {
        this.input.disconnect();
        this.processor.disconnect();
      } catch (e) {}
    }
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach((t) => t.stop());
    }
    if (this.audioContext && this.audioContext.state !== "closed") {
      try {
        await this.audioContext.close();
      } catch (e) {}
    }

    // Flatten all Float32Array chunks into a single array
    let totalLength = 0;
    for (const chunk of this.pcmChunks) {
      totalLength += chunk.length;
    }
    const mergedSamples = new Float32Array(totalLength);
    let offset = 0;
    for (const chunk of this.pcmChunks) {
      mergedSamples.set(chunk, offset);
      offset += chunk.length;
    }

    return this.encodeWAV(mergedSamples, this.sampleRate);
  }

  encodeWAV(samples, sampleRate) {
    const buffer = new ArrayBuffer(44 + samples.length * 2);
    const view = new DataView(buffer);

    const writeString = (view, offset, str) => {
      for (let i = 0; i < str.length; i++) {
        view.setUint8(offset + i, str.charCodeAt(i));
      }
    };

    // RIFF identifier
    writeString(view, 0, "RIFF");
    // file length
    view.setUint32(4, 36 + samples.length * 2, true);
    // RIFF type
    writeString(view, 8, "WAVE");
    // format chunk identifier
    writeString(view, 12, "fmt ");
    // format chunk length
    view.setUint32(16, 16, true);
    // sample format (1 = linear PCM)
    view.setUint16(20, 1, true);
    // channel count (1 = mono)
    view.setUint16(22, 1, true);
    // sample rate
    view.setUint32(24, sampleRate, true);
    // byte rate (sampleRate * 2 for 16-bit mono)
    view.setUint32(28, sampleRate * 2, true);
    // block align (2 bytes)
    view.setUint16(32, 2, true);
    // bits per sample (16 bits)
    view.setUint16(34, 16, true);
    // data chunk identifier
    writeString(view, 36, "data");
    // data chunk length
    view.setUint32(40, samples.length * 2, true);

    // Write 16-bit PCM samples
    let dataOffset = 44;
    for (let i = 0; i < samples.length; i++, dataOffset += 2) {
      const s = Math.max(-1, Math.min(1, samples[i]));
      view.setInt16(dataOffset, s < 0 ? s * 0x8000 : s * 0x7fff, true);
    }

    return new Blob([view], { type: "audio/wav" });
  }
}

class VoiceManager {
  constructor() {
    this.isRecording = false;
    this.activeRecognitionInstance = null;
    this.silenceTimeout = null;
    this.pcmRecorder = null;
    this.currentTargetInput = null;
    this.activeStatusCallback = null;

    this.synth = window.speechSynthesis || null;
    this.voices = [];
    this.currentUtterance = null;
    this.audioElement = null; // Active HTML5 Audio instance for Blob MP3
    this.currentBlobUrl = null;
    this.isSpeaking = false;
    this.isPaused = false;
    this.activeAudioMode = "server";

    // Persisted settings
    this.voiceOutputEnabled = localStorage.getItem("autoassist_voice_enabled") !== "false";
    this.speechRate = parseFloat(localStorage.getItem("autoassist_voice_rate") || "1.0");
    this.speechPitch = parseFloat(localStorage.getItem("autoassist_voice_pitch") || "1.0");
    this.selectedVoiceURI = localStorage.getItem("autoassist_voice_uri") || null;

    // Standard BCP-47 Locale map
    this.langMap = {
      en: "en-IN",
      kn: "kn-IN",
      hi: "hi-IN",
      ur: "ur-IN",
      ml: "ml-IN",
      ta: "ta-IN",
      te: "te-IN",
    };

    // User-friendly Language Names
    this.langNames = {
      en: "English",
      kn: "ಕನ್ನಡ (Kannada)",
      hi: "हिन्दी (Hindi)",
      ur: "اردو (Urdu)",
      ml: "മലയാളം (Malayalam)",
      ta: "தமிழ் (Tamil)",
      te: "తెలుగు (Telugu)",
    };

    this._initSpeechSynthesis();
  }

  // =========================================================================
  // 1. SPEECH RECOGNITION (VOICE INPUT / STT)
  // =========================================================================
  isSpeechRecognitionSupported() {
    return !!(window.SpeechRecognition || window.webkitSpeechRecognition);
  }

  _getOrCreateFloatingBanner() {
    let banner = document.getElementById("voice-recording-banner");
    if (!banner) {
      banner = document.createElement("div");
      banner.id = "voice-recording-banner";
      banner.style.position = "fixed";
      banner.style.bottom = "24px";
      banner.style.left = "50%";
      banner.style.transform = "translateX(-50%)";
      banner.style.zIndex = "99999";
      banner.style.padding = "0.75rem 1.4rem";
      banner.style.borderRadius = "30px";
      banner.style.background = "linear-gradient(135deg, #1e293b, #0f172a)";
      banner.style.border = "1px solid rgba(56, 189, 248, 0.4)";
      banner.style.boxShadow = "0 10px 25px -5px rgba(0, 0, 0, 0.6), 0 0 15px rgba(56, 189, 248, 0.3)";
      banner.style.color = "#ffffff";
      banner.style.fontSize = "0.88rem";
      banner.style.fontWeight = "600";
      banner.style.display = "none";
      banner.style.alignItems = "center";
      banner.style.gap = "0.75rem";
      banner.style.transition = "all 0.3s ease";
      document.body.appendChild(banner);
    }
    return banner;
  }

  _showRecordingBanner(langName, text = "") {
    const banner = this._getOrCreateFloatingBanner();
    banner.style.display = "flex";
    banner.innerHTML = `
      <span style="display: inline-block; width: 12px; height: 12px; border-radius: 50%; background: #ef4444; animation: micPulse 1.2s infinite;"></span>
      <span>🎙️ Listening in <strong>${langName}</strong>: <span style="color: #38bdf8;">${text || "Speak your vehicle symptom now..."}</span></span>
      <button type="button" style="background: rgba(255,255,255,0.18); border: 1px solid rgba(255,255,255,0.3); color: #fff; border-radius: 12px; padding: 3px 10px; cursor: pointer; font-size: 0.75rem; margin-left: 0.5rem; font-weight: 700;" onclick="window.voiceManager.stopListening()">Finish ⏹️</button>
    `;
  }

  _hideRecordingBanner() {
    const banner = document.getElementById("voice-recording-banner");
    if (banner) {
      banner.style.display = "none";
    }
  }

  _resetSilenceTimer() {
    if (this.silenceTimeout) {
      clearTimeout(this.silenceTimeout);
    }
    // Automatically finalize after 3.5s silence after speech was captured
    this.silenceTimeout = setTimeout(() => {
      console.log("[VoiceManager] Speech silence detected. Finalizing transcription.");
      this.stopListening();
    }, 3500);
  }

  startListening(targetInputElement, onStatusChange = null) {
    const targetEl = typeof targetInputElement === "string" ? document.getElementById(targetInputElement) : targetInputElement;

    if (this.isRecording) {
      this.stopListening();
      if (onStatusChange) onStatusChange(false, "stopped");
      return;
    }

    this.currentTargetInput = targetEl;
    this.activeStatusCallback = onStatusChange;

    const currentLang = (window.i18n && window.i18n.currentLang) || "en";
    const bcp47 = this.langMap[currentLang] || "en-IN";
    const langLabel = this.langNames[currentLang] || "English";

    // 1. Primary: Native Web Speech API
    if (this.isSpeechRecognitionSupported()) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

      try {
        if (this.activeRecognitionInstance) {
          try {
            this.activeRecognitionInstance.abort();
          } catch (e) {}
        }

        const rec = new SpeechRecognition();
        rec.lang = bcp47;
        rec.continuous = true;
        rec.interimResults = true;
        rec.maxAlternatives = 1;

        const initialText = targetEl && targetEl.value ? targetEl.value.trim() : "";
        const originalPlaceholder = targetEl ? targetEl.placeholder : "";

        rec.onstart = () => {
          this.isRecording = true;
          this._showRecordingBanner(langLabel);
          if (targetEl) {
            targetEl.placeholder = `🎙️ Listening in ${langLabel}... Speak now! (Click ⏹️ when finished)`;
          }
          console.log(`[VoiceManager] Speech recognition started. Locale: ${bcp47}`);
          if (onStatusChange) onStatusChange(true, "listening");
        };

        rec.onresult = (event) => {
          let fullFinal = "";
          let fullInterim = "";

          // Accumulate cleanly from 0 to results.length
          for (let i = 0; i < event.results.length; ++i) {
            const res = event.results[i];
            if (res.isFinal) {
              fullFinal += res[0].transcript + " ";
            } else {
              fullInterim += res[0].transcript;
            }
          }

          const currentTranscript = (fullFinal + fullInterim).trim();
          this._showRecordingBanner(langLabel, currentTranscript);

          // Real-time text injection directly into the input box
          if (targetEl && currentTranscript) {
            targetEl.value = initialText ? `${initialText} ${currentTranscript}` : currentTranscript;
            targetEl.dispatchEvent(new Event("input", { bubbles: true }));
          }

          if (currentTranscript.length > 0) {
            this._resetSilenceTimer();
          }
        };

        rec.onerror = (event) => {
          console.warn("[VoiceManager] Speech recognition error:", event.error);
          if (event.error === "no-speech") {
            // Keep listening; user is pausing or preparing to speak
            return;
          }

          this._hideRecordingBanner();
          if (targetEl && originalPlaceholder) {
            targetEl.placeholder = originalPlaceholder;
          }

          if (event.error === "not-allowed" || event.error === "service-not-allowed") {
            this.isRecording = false;
            if (onStatusChange) onStatusChange(false, event.error);
            alert("Microphone permission was denied. Please allow microphone access in your browser address bar.");
          } else if (event.error === "network") {
            console.warn("[VoiceManager] Web Speech network error. Switching to PCM WAV Google STT engine...");
            this._startPcmAudioListening(targetEl, currentLang, langLabel, onStatusChange);
          } else {
            this.isRecording = false;
            if (onStatusChange) onStatusChange(false, event.error);
          }
        };

        rec.onend = () => {
          this.isRecording = false;
          this.activeRecognitionInstance = null;
          this._hideRecordingBanner();
          if (this.silenceTimeout) clearTimeout(this.silenceTimeout);
          if (targetEl && originalPlaceholder) {
            targetEl.placeholder = originalPlaceholder;
          }
          console.log("[VoiceManager] Speech recognition ended.");
          if (onStatusChange) onStatusChange(false, "idle");

          // Auto-submit when voice query is captured
          if (targetEl && targetEl.value && targetEl.value.trim().length > 3 && targetEl.form) {
            setTimeout(() => {
              targetEl.form.dispatchEvent(new Event("submit", { cancelable: true }));
            }, 300);
          }
        };

        this.activeRecognitionInstance = rec;
        rec.start();
        return;
      } catch (err) {
        console.warn("[VoiceManager] Web Speech exception, switching to PCM WAV fallback:", err);
      }
    }

    // 2. High-Accuracy PCM WAV Speech Recognition Fallback
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      this._startPcmAudioListening(targetEl, currentLang, langLabel, onStatusChange);
      return;
    }

    alert(
      "Voice recognition is not supported in this browser.\n\n" +
      "Please use Google Chrome, Microsoft Edge, or a browser with microphone support."
    );
    if (onStatusChange) onStatusChange(false, "unsupported");
  }

  async _startPcmAudioListening(targetEl, currentLang, langLabel, onStatusChange) {
    try {
      this.pcmRecorder = new PcmWavRecorder();
      await this.pcmRecorder.start();

      this.isRecording = true;
      this._showRecordingBanner(langLabel, "Listening to microphone audio...");
      if (onStatusChange) onStatusChange(true, "listening");

      const originalPlaceholder = targetEl ? targetEl.placeholder : "";
      if (targetEl) {
        targetEl.placeholder = `🎙️ Listening in ${langLabel}... Speak now! (Click ⏹️ when finished)`;
      }
    } catch (err) {
      console.error("[VoiceManager] Microphone access error:", err);
      this.isRecording = false;
      this._hideRecordingBanner();
      if (onStatusChange) onStatusChange(false, "denied");
      alert("Microphone permission was denied. Please allow microphone permissions in browser settings.");
    }
  }

  async stopListening() {
    this._hideRecordingBanner();
    if (this.silenceTimeout) {
      clearTimeout(this.silenceTimeout);
      this.silenceTimeout = null;
    }

    // 1. Stop Native Web Speech
    if (this.activeRecognitionInstance) {
      try {
        this.activeRecognitionInstance.stop();
      } catch (e) {
        try {
          this.activeRecognitionInstance.abort();
        } catch (inner) {}
      }
      this.activeRecognitionInstance = null;
    }

    // 2. Stop PCM WAV Recorder and transcribe real spoken words
    if (this.pcmRecorder) {
      const recorder = this.pcmRecorder;
      this.pcmRecorder = null;
      this.isRecording = false;

      const currentLang = (window.i18n && window.i18n.currentLang) || "en";
      const langLabel = this.langNames[currentLang] || "English";
      const targetEl = this.currentTargetInput;
      const callback = this.activeStatusCallback;

      this._showRecordingBanner(langLabel, "Transcribing words...");

      try {
        const wavBlob = await recorder.stop();

        // Send true 16kHz PCM WAV to server-side Google Speech API
        const formData = new FormData();
        formData.append("audio", wavBlob, "speech.wav");
        formData.append("lang", currentLang);

        const resp = await fetch("/api/voice/transcribe", {
          method: "POST",
          body: formData,
        });

        const data = await resp.json();
        if (data.transcription && data.transcription.trim()) {
          const text = data.transcription.trim();
          if (targetEl) {
            const currentVal = targetEl.value ? targetEl.value.trim() : "";
            targetEl.value = currentVal ? `${currentVal} ${text}` : text;
            targetEl.dispatchEvent(new Event("input", { bubbles: true }));

            // Auto-submit when voice query is captured
            if (targetEl.value.trim().length > 3 && targetEl.form) {
              setTimeout(() => {
                targetEl.form.dispatchEvent(new Event("submit", { cancelable: true }));
              }, 400);
            }
          }
          this._showRecordingBanner(langLabel, `Recognized: "${text}"`);
          setTimeout(() => this._hideRecordingBanner(), 2500);
        } else if (data.error) {
          this._showRecordingBanner(langLabel, `⚠️ ${data.error}`);
          setTimeout(() => this._hideRecordingBanner(), 3000);
        } else {
          this._hideRecordingBanner();
        }
      } catch (e) {
        console.error("[VoiceManager] Server transcription error:", e);
        this._hideRecordingBanner();
      }

      if (callback) callback(false, "idle");
      return;
    }

    this.isRecording = false;
  }

  // =========================================================================
  // 2. SPEECH SYNTHESIS (VOICE OUTPUT / TTS)
  // =========================================================================
  _initSpeechSynthesis() {
    if (!this.synth) return;

    const loadVoices = () => {
      try {
        this.voices = this.synth.getVoices() || [];
        this._populateVoiceSelector();
      } catch (e) {
        console.warn("[VoiceManager] Could not load browser voices:", e);
      }
    };

    loadVoices();
    if (this.synth.onvoiceschanged !== undefined) {
      this.synth.onvoiceschanged = loadVoices;
    }
  }

  _populateVoiceSelector() {
    const selector = document.getElementById("settings-voice-select");
    if (!selector) return;

    selector.innerHTML = "";
    const defaultOpt = document.createElement("option");
    defaultOpt.value = "";
    defaultOpt.textContent = "Automatic Voice (Native Regional Engine)";
    selector.appendChild(defaultOpt);

    const currentLang = (window.i18n && window.i18n.currentLang) || "en";
    const targetPrefix = currentLang.toLowerCase();

    const matchingVoices = this.voices.filter((v) => v.lang.toLowerCase().startsWith(targetPrefix));
    const listToRender = matchingVoices.length > 0 ? matchingVoices : this.voices;

    listToRender.forEach((v) => {
      const opt = document.createElement("option");
      opt.value = v.voiceURI;
      opt.textContent = `${v.name} (${v.lang})`;
      if (v.voiceURI === this.selectedVoiceURI) {
        opt.selected = true;
      }
      selector.appendChild(opt);
    });
  }

  updateLanguage(langCode) {
    this._populateVoiceSelector();
  }

  async speak(text, customLang = null, onStateChange = null) {
    this.stopSpeaking();

    // Polymorphic argument handling: speak(text, callback) or speak(text, lang, callback)
    let lang = customLang;
    let callback = onStateChange;
    if (typeof customLang === "function") {
      callback = customLang;
      lang = null;
    }

    // Always enable voice output when speak() is explicitly requested
    this.voiceOutputEnabled = true;

    const cleanText = String(text)
      .replace(/[#*`_~]/g, "")
      .replace(/https?:\/\/\S+/g, "")
      .replace(/₹/g, " Rupees ")
      .replace(/⚠️|🛑|💡|🔍|🔧/g, "")
      .trim();

    if (!cleanText) return;

    const currentLang = (typeof lang === "string" && lang) ? lang : ((window.i18n && window.i18n.currentLang) || "en");
    const targetLocale = this.langMap[currentLang] || "en-IN";

    // Unfreeze Chrome SpeechSynthesis if stalled
    if (this.synth) {
      try {
        this.synth.cancel();
        if (this.synth.paused) {
          this.synth.resume();
        }
      } catch (e) {}
    }

    // Check if browser has a native voice installed for this language
    let matchingVoice = null;
    if (this.voices && this.voices.length > 0) {
      if (this.selectedVoiceURI) {
        matchingVoice = this.voices.find((v) => v.voiceURI === this.selectedVoiceURI);
      }
      if (!matchingVoice) {
        matchingVoice = this.voices.find(
          (v) => v.lang.toLowerCase() === targetLocale.toLowerCase() || (v.lang.toLowerCase().startsWith(currentLang) && currentLang !== "en")
        );
      }
    }

    // If English and browser has voice, use browser SpeechSynthesis
    if (this.synth && currentLang === "en" && matchingVoice) {
      try {
        this.activeAudioMode = "browser";
        const utterance = new SpeechSynthesisUtterance(cleanText);
        utterance.rate = this.speechRate;
        utterance.pitch = this.speechPitch;
        utterance.lang = targetLocale;
        if (matchingVoice) utterance.voice = matchingVoice;

        utterance.onstart = () => {
          this.isSpeaking = true;
          this.isPaused = false;
          if (callback) {
            callback("start");
            callback("playing");
          }
        };

        utterance.onend = () => {
          this.isSpeaking = false;
          this.isPaused = false;
          this.currentUtterance = null;
          if (callback) {
            callback("end");
            callback("stopped");
          }
        };

        utterance.onerror = (e) => {
          console.warn("[VoiceManager] Browser speech error, using server fallback:", e);
          this._speakViaServerBlob(cleanText, currentLang, callback);
        };

        window._activeSpeechUtterance = utterance;
        this.currentUtterance = utterance;
        this.synth.speak(utterance);
        return;
      } catch (err) {
        console.warn("[VoiceManager] synth.speak threw error, using server fallback:", err);
      }
    }

    // High-Fidelity Server-side MP3 Blob Audio Player (guarantees crystal-clear audio for kn, hi, ur, ml, ta, te)
    await this._speakViaServerBlob(cleanText, currentLang, callback);
  }

  async _speakViaServerBlob(text, lang, onStateChange = null) {
    this.activeAudioMode = "server";

    if (this.audioElement) {
      try {
        this.audioElement.pause();
      } catch (e) {}
      this.audioElement = null;
    }
    if (this.currentBlobUrl) {
      try {
        URL.revokeObjectURL(this.currentBlobUrl);
      } catch (e) {}
      this.currentBlobUrl = null;
    }

    if (onStateChange) onStateChange("loading");

    try {
      const speakSlice = text.length > 500 ? text.substring(0, 500) : text;

      // Use POST with JSON body: completely eliminates URL character length limits for Indian scripts
      const resp = await fetch("/api/voice/synthesize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: speakSlice, lang: lang }),
      });

      if (!resp.ok) {
        throw new Error(`Server returned HTTP ${resp.status}`);
      }

      const audioBlob = await resp.blob();
      const blobUrl = URL.createObjectURL(audioBlob);
      this.currentBlobUrl = blobUrl;

      const audio = new Audio(blobUrl);
      audio.playbackRate = this.speechRate;

      audio.onplay = () => {
        this.isSpeaking = true;
        this.isPaused = false;
        if (onStateChange) {
          onStateChange("start");
          onStateChange("playing");
        }
      };

      audio.onended = () => {
        this.isSpeaking = false;
        this.isPaused = false;
        this.audioElement = null;
        if (onStateChange) {
          onStateChange("end");
          onStateChange("stopped");
        }
      };

      audio.onerror = (err) => {
        console.warn("[VoiceManager] Audio playback error:", err);
        this.isSpeaking = false;
        this.isPaused = false;
        this.audioElement = null;
        if (onStateChange) onStateChange("error");
      };

      this.audioElement = audio;
      await audio.play();
    } catch (err) {
      console.warn("[VoiceManager] Server speech playback error, attempting browser TTS fallback:", err);

      // Browser TTS Fallback if network/server is unavailable
      if (this.synth) {
        try {
          const utterance = new SpeechSynthesisUtterance(text);
          utterance.lang = this.langMap[lang] || "en-IN";
          utterance.rate = this.speechRate;
          utterance.onstart = () => {
            this.isSpeaking = true;
            if (onStateChange) onStateChange("playing");
          };
          utterance.onend = () => {
            this.isSpeaking = false;
            if (onStateChange) onStateChange("stopped");
          };
          utterance.onerror = () => {
            this.isSpeaking = false;
            if (onStateChange) onStateChange("error");
          };
          this.synth.speak(utterance);
          return;
        } catch (inner) {}
      }

      this.isSpeaking = false;
      this.isPaused = false;
      if (onStateChange) onStateChange("error");
    }
  }

  pauseSpeaking(onStateChange = null) {
    if (this.activeAudioMode === "server" && this.audioElement) {
      this.audioElement.pause();
      this.isPaused = true;
      if (onStateChange) onStateChange("paused");
      return;
    }

    if (this.synth && this.isSpeaking && !this.isPaused) {
      try {
        this.synth.pause();
        this.isPaused = true;
        if (onStateChange) onStateChange("paused");
      } catch (e) {}
    }
  }

  resumeSpeaking(onStateChange = null) {
    if (this.activeAudioMode === "server" && this.audioElement && this.isPaused) {
      this.audioElement.play();
      this.isPaused = false;
      if (onStateChange) onStateChange("playing");
      return;
    }

    if (this.synth && this.isSpeaking && this.isPaused) {
      try {
        this.synth.resume();
        this.isPaused = false;
        if (onStateChange) onStateChange("playing");
      } catch (e) {}
    }
  }

  stopSpeaking(onStateChange = null) {
    if (this.audioElement) {
      try {
        this.audioElement.pause();
        this.audioElement.currentTime = 0;
      } catch (e) {}
      this.audioElement = null;
    }

    if (this.currentBlobUrl) {
      try {
        URL.revokeObjectURL(this.currentBlobUrl);
      } catch (e) {}
      this.currentBlobUrl = null;
    }

    if (this.synth) {
      try {
        this.synth.cancel();
      } catch (e) {}
    }

    this.isSpeaking = false;
    this.isPaused = false;
    this.currentUtterance = null;
    if (onStateChange) onStateChange("stopped");
  }

  setRate(rate) {
    this.speechRate = parseFloat(rate) || 1.0;
    localStorage.setItem("autoassist_voice_rate", this.speechRate);
    if (this.audioElement) {
      this.audioElement.playbackRate = this.speechRate;
    }
  }

  setPitch(pitch) {
    this.speechPitch = parseFloat(pitch) || 1.0;
    localStorage.setItem("autoassist_voice_pitch", this.speechPitch);
  }

  setVoice(voiceURI) {
    this.selectedVoiceURI = voiceURI;
    localStorage.setItem("autoassist_voice_uri", voiceURI);
  }

  toggleVoiceOutput(enabled) {
    this.voiceOutputEnabled = !!enabled;
    localStorage.setItem("autoassist_voice_enabled", this.voiceOutputEnabled);
    if (!this.voiceOutputEnabled) {
      this.stopSpeaking();
    }
  }

  // Method Aliases for backward compatibility
  setSpeechRate(rate) {
    this.setRate(rate);
  }

  setSpeechPitch(pitch) {
    this.setPitch(pitch);
  }

  setVoiceURI(voiceURI) {
    this.setVoice(voiceURI);
  }

  setVoiceOutputEnabled(enabled) {
    this.toggleVoiceOutput(enabled);
  }

  pause() {
    this.pauseSpeaking();
  }

  resume() {
    this.resumeSpeaking();
  }

  stop() {
    this.stopSpeaking();
  }
}

window.voiceManager = new VoiceManager();

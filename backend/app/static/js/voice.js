/**
 * AutoAssist AI - Voice Input (Speech-to-Text) & Voice Output (Text-to-Speech) Engine
 * Powered by Web Speech API & SpeechSynthesis API
 */

class VoiceManager {
  constructor() {
    this.recognition = null;
    this.isRecording = false;
    this.synth = window.speechSynthesis || null;
    this.voices = [];
    this.currentUtterance = null;
    this.isSpeaking = false;
    this.isPaused = false;

    // Load persisted settings
    this.voiceOutputEnabled = localStorage.getItem("autoassist_voice_enabled") !== "false";
    this.speechRate = parseFloat(localStorage.getItem("autoassist_voice_rate") || "1.0");
    this.speechPitch = parseFloat(localStorage.getItem("autoassist_voice_pitch") || "1.0");
    this.selectedVoiceURI = localStorage.getItem("autoassist_voice_uri") || null;

    this.langMap = {
      en: "en-US",
      kn: "kn-IN",
      hi: "hi-IN",
      ur: "ur-PK",
      ml: "ml-IN",
      ta: "ta-IN",
      te: "te-IN"
    };

    this._initSpeechRecognition();
    this._initSpeechSynthesis();
  }

  // =========================================================================
  // 1. SPEECH RECOGNITION (VOICE INPUT)
  // =========================================================================
  _initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition || null;
    if (!SpeechRecognition) {
      console.warn("Speech recognition is not supported in this browser.");
      return;
    }

    try {
      this.recognition = new SpeechRecognition();
      this.recognition.continuous = false;
      this.recognition.interimResults = true;
      this.recognition.maxAlternatives = 1;
    } catch (e) {
      console.warn("Failed to instantiate SpeechRecognition:", e);
    }
  }

  isSpeechRecognitionSupported() {
    return !!(window.SpeechRecognition || window.webkitSpeechRecognition);
  }

  startListening(targetInputElement, onStatusChange) {
    if (!this.isSpeechRecognitionSupported()) {
      alert("Voice input is not supported in this browser. Please use Chrome, Edge, or Safari.");
      return;
    }

    if (this.isRecording) {
      this.stopListening();
      return;
    }

    const currentLang = (window.i18n && window.i18n.currentLang) || "en";
    const bcp47 = this.langMap[currentLang] || "en-US";
    this.recognition.lang = bcp47;

    const initialText = targetInputElement.value || "";
    let finalTranscript = "";

    this.recognition.onstart = () => {
      this.isRecording = true;
      if (onStatusChange) onStatusChange(true, "listening");
    };

    this.recognition.onresult = (event) => {
      let interim = "";
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
        } else {
          interim += event.results[i][0].transcript;
        }
      }
      const combined = (initialText ? initialText + " " : "") + (finalTranscript || interim);
      targetInputElement.value = combined;
      targetInputElement.dispatchEvent(new Event("input", { bubbles: true }));
    };

    this.recognition.onerror = (event) => {
      console.warn("Speech recognition error:", event.error);
      this.isRecording = false;
      if (onStatusChange) onStatusChange(false, event.error);
      if (event.error === "not-allowed") {
        alert("Microphone permission was denied. Please allow microphone access in your browser settings to use voice input.");
      }
    };

    this.recognition.onend = () => {
      this.isRecording = false;
      if (onStatusChange) onStatusChange(false, "idle");
    };

    try {
      this.recognition.start();
    } catch (err) {
      console.warn("Could not start recognition:", err);
      this.isRecording = false;
      if (onStatusChange) onStatusChange(false, "error");
    }
  }

  stopListening() {
    if (this.recognition && this.isRecording) {
      try {
        this.recognition.stop();
      } catch (e) {
        console.warn("Could not stop recognition:", e);
      }
      this.isRecording = false;
    }
  }

  // =========================================================================
  // 2. SPEECH SYNTHESIS (VOICE OUTPUT)
  // =========================================================================
  _initSpeechSynthesis() {
    if (!this.synth) return;

    const loadVoices = () => {
      this.voices = this.synth.getVoices() || [];
      this._populateVoiceSelector();
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
    const currentLang = (window.i18n && window.i18n.currentLang) || "en";
    const targetPrefix = currentLang.toLowerCase();

    // Prioritize voices for current language
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

  speak(text, onStateChange = null) {
    if (!this.synth || !this.voiceOutputEnabled) return;
    this.stopSpeaking();

    // Clean text for speech (strip markdown symbols)
    const cleanText = text
      .replace(/[#*`_~]/g, "")
      .replace(/https?:\/\/\S+/g, "")
      .replace(/₹/g, " Rupees ")
      .trim();

    if (!cleanText) return;

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.rate = this.speechRate;
    utterance.pitch = this.speechPitch;

    const currentLang = (window.i18n && window.i18n.currentLang) || "en";
    utterance.lang = this.langMap[currentLang] || "en-US";

    // Set voice if chosen
    if (this.selectedVoiceURI) {
      const chosen = this.voices.find((v) => v.voiceURI === this.selectedVoiceURI);
      if (chosen) utterance.voice = chosen;
    } else {
      const best = this.voices.find((v) => v.lang.toLowerCase().startsWith(currentLang));
      if (best) utterance.voice = best;
    }

    utterance.onstart = () => {
      this.isSpeaking = true;
      this.isPaused = false;
      if (onStateChange) onStateChange("playing");
    };

    utterance.onend = () => {
      this.isSpeaking = false;
      this.isPaused = false;
      this.currentUtterance = null;
      if (onStateChange) onStateChange("stopped");
    };

    utterance.onerror = () => {
      this.isSpeaking = false;
      this.isPaused = false;
      this.currentUtterance = null;
      if (onStateChange) onStateChange("stopped");
    };

    this.currentUtterance = utterance;
    this.synth.speak(utterance);
  }

  pauseSpeaking(onStateChange = null) {
    if (this.synth && this.isSpeaking && !this.isPaused) {
      this.synth.pause();
      this.isPaused = true;
      if (onStateChange) onStateChange("paused");
    }
  }

  resumeSpeaking(onStateChange = null) {
    if (this.synth && this.isSpeaking && this.isPaused) {
      this.synth.resume();
      this.isPaused = false;
      if (onStateChange) onStateChange("playing");
    }
  }

  stopSpeaking(onStateChange = null) {
    if (this.synth) {
      this.synth.cancel();
      this.isSpeaking = false;
      this.isPaused = false;
      this.currentUtterance = null;
      if (onStateChange) onStateChange("stopped");
    }
  }

  setRate(rate) {
    this.speechRate = parseFloat(rate);
    localStorage.setItem("autoassist_voice_rate", this.speechRate);
  }

  setPitch(pitch) {
    this.speechPitch = parseFloat(pitch);
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
}

window.voiceManager = new VoiceManager();

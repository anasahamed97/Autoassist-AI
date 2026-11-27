/**
 * AutoAssist AI - Complete Automotive Diagnostic & Service Platform Client Logic
 * Integrates:
 * 1. Multilingual Support (en, hi, kn, ar, ur) + RTL
 * 2. Voice Input (Speech-to-Text) & Voice Output (Text-to-Speech)
 * 3. Intelligent Manual Search with Dual-View (Technical vs Simple Words) + Ask Your Mechanic
 * 4. AI Repair Cost Estimator in INR (₹)
 * 5. Mechanic Quotation Checker with Verified Benchmarks
 * 6. Vehicle Profile Management (CRUD + Active Default)
 * 7. Problem Severity Assessment (LOW, MODERATE, CRITICAL)
 * 8. Preventive Maintenance Tracker
 * 9. All 8 Specialized Diagnostic Analyzers & 1-Click Simulations
 */

// ==========================================================================
// Global Application State
// ==========================================================================
const state = {
  activeSection: "dashboard",
  manualViewMode: "simple", // "simple" or "technical"
  activeVehicle: {
    id: "default_civic",
    make: "Honda",
    model: "Civic",
    year: 2022,
    fuel_type: "Petrol",
    mileage_km: 45000,
    city: "Bengaluru",
    is_default: true,
  },
  vehiclesList: [],
  lastResult: null,
  manualResult: null,
  wizard: {
    domain: null,
    questions: [],
    currentStep: 0,
    answers: {},
  },
};

// ==========================================================================
// Initialization on DOM Ready
// ==========================================================================
document.addEventListener("DOMContentLoaded", () => {
  initI18nAndLanguage();
  initVoiceControls();
  initNavigation();
  initTheme();
  initVehiclesModule();
  initMaintenanceModule();
  initAssistantChat();
  initManualsSearch();
  initCostEstimator();
  initQuotationChecker();
  initSettingsPanel();

  // Initialize specialized diagnostic analyzers
  initDTCScanner();
  initElectricalAnalyzer();
  initThermalAnalyzer();
  initBrakeAnalyzer();
  initDrivetrainAnalyzer();
  initEmissionsAnalyzer();
  initWizard();
  initWorkOrderModal();

  // Initial load
  loadVehicles();
  loadMaintenanceOverview();
});

// ==========================================================================
// 1. Navigation Between 8 Primary Sections
// ==========================================================================
function initNavigation() {
  const navBtns = document.querySelectorAll("#main-nav-links .nav-link");
  navBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      const targetSec = btn.dataset.section;
      if (targetSec) navigateToSection(targetSec);
    });
  });
}

window.navigateToSection = function (sectionId) {
  state.activeSection = sectionId;

  // Toggle active class on nav buttons
  const navBtns = document.querySelectorAll("#main-nav-links .nav-link");
  navBtns.forEach((b) => {
    if (b.dataset.section === sectionId) b.classList.add("active");
    else b.classList.remove("active");
  });

  // Toggle view sections
  const sections = document.querySelectorAll(".view-section");
  sections.forEach((sec) => {
    if (sec.id === `view-${sectionId}`) {
      sec.classList.add("active");
      sec.style.display = "block";
    } else {
      sec.classList.remove("active");
      sec.style.display = "none";
    }
  });

  window.scrollTo({ top: 0, behavior: "smooth" });

  // Refresh relevant data when entering view
  if (sectionId === "vehicles") loadVehicles();
  if (sectionId === "maintenance") loadMaintenanceOverview();
};

// Sub-Tab Switcher for AI Assistant's 8 Diagnostic Analyzers
window.switchStudioTab = function (tabId) {
  const tabBtns = document.querySelectorAll(".tab-btn");
  const tabPanels = document.querySelectorAll(".tab-panel");

  tabBtns.forEach((b) => {
    if (b.getAttribute("data-tab") === tabId) b.classList.add("active");
    else b.classList.remove("active");
  });

  tabPanels.forEach((p) => {
    if (p.id === tabId) {
      p.classList.add("active");
      p.style.display = "block";
    } else {
      p.classList.remove("active");
      p.style.display = "none";
    }
  });
};

// Multilingual Quick Test Chips for AI Assistant input
const MULTILINGUAL_EXAMPLE_CHIPS = {
  en: [
    { label: "Overheating & Bubbling", q: "Engine overheating rapidly with bubbling coolant" },
    { label: "Brake Pedal Sinking", q: "Brake pedal sinking to floor when stopped" },
    { label: "Serpentine Belt Squeal", q: "High-pitched squeal when accelerating in morning" },
    { label: "Dead Battery Clicking", q: "Rapid clicking sound when turning key won't start" },
  ],
  kn: [
    { label: "🔥 ಎಂಜಿನ್ ಬಿಸಿಯಾಗುತ್ತಿದೆ", q: "ಎಂಜಿನ್ ಅತಿಯಾಗಿ ಬಿಸಿಯಾಗುತ್ತಿದೆ ಮತ್ತು ಕೂಲೆಂಟ್ ಕುದಿಯುತ್ತಿದೆ" },
    { label: "🛑 ಬ್ರೇಕ್ ಪೆಡಲ್ ಕುಸಿತ", q: "ಬ್ರೇಕ್ ಹಾಕಿದಾಗ ಪೆಡಲ್ ನೆಲಕ್ಕೆ ಕುಸಿಯುತ್ತಿದೆ" },
    { label: "🔋 ಬ್ಯಾಟರಿ ಡೆಡ್ - ಕ್ಲಿಕ್ ಶಬ್ದ", q: "ಕೀ ತಿರುಗಿಸಿದಾಗ ಕೇವಲ ಕ್ಲಿಕ್ ಶಬ್ದ ಬರ್ತಿದೆ ಗಾಡಿ ಸ್ಟಾರ್ಟ್ ಆಗ್ತಿಲ್ಲ" },
    { label: "⚡ ಚೆಕ್ ಎಂಜಿನ್ ಲೈಟ್", q: "ಚೆಕ್ ಎಂಜಿನ್ ಲೈಟ್ ಉರಿಯುತ್ತಿದೆ ಮತ್ತು ಎಂಜಿನ್ ನಡುಗುತ್ತಿದೆ" },
  ],
  hi: [
    { label: "🔥 इंजन बहुत गरम हो रहा है", q: "इंजन बहुत अधिक गरम हो रहा है और धुआं निकल रहा है" },
    { label: "🛑 ब्रेक पेडल नीचे धंस रहा है", q: "ब्रेक लगाने पर पेडल फर्श तक धंस जाता है" },
    { label: "🔋 बैटरी डिस्चार्ज - टिक-टिक", q: "चाबी घुमाने पर सिर्फ टिक टिक आवाज़ आ रही है गाड़ी स्टार्ट नहीं हो रही" },
    { label: "⚡ चेक इंजन लाइट", q: "चेक इंजन लाइट जल रही है और गाड़ी झटका ले रही है" },
  ],
  ur: [
    { label: "🔥 انجن زیادہ گرم ہو رہا ہے", q: "گاڑی کا انجن بہت زیادہ گرم ہو رہا ہے اور ریڈی ایٹر ابل رہا ہے" },
    { label: "🛑 بریک پیڈل دب رہا ہے", q: "بریک دبانے پر پیڈل بالکل نیچے چلا جاتا ہے" },
    { label: "🔋 بیٹری ڈیڈ - کلک کی آواز", q: "چابی گھمانے پر کلک کی آواز آ رہی ہے گاڑی سٹارٹ نہیں ہو رہی" },
  ],
  ml: [
    { label: "🔥 എഞ്ചിൻ അമിതമായി ചൂടാകുന്നു", q: "എഞ്ചിൻ അമിതമായി ചൂടാകുന്നു കൂളന്റ് തിളയ്ക്കുന്നു" },
    { label: "🛑 ബ്രേക്ക് പെഡൽ താഴേക്ക് പോകുന്നു", q: "ബ്രേക്ക് പെഡൽ അമർത്തുമ്പോൾ താഴേക്ക് പോവുന്നു" },
    { label: "🔋 ബാറ്ററി ഡിസ്ചാർജ്", q: "കീ തിരിക്കുമ്പോൾ ക്ലിക്ക് ശബ്ദം മാത്രം വാഹനം സ്റ്റാർട്ടാവുന്നില്ല" },
  ],
  ta: [
    { label: "🔥 என்ஜின் அதிக வெப்பமடைகிறது", q: "என்ஜின் அதிக வெப்பமடைகிறது மற்றும் கூலன்ட் கொதிக்கிறது" },
    { label: "🛑 பிரேக் பெடல் கீழே இறங்குகிறது", q: "பிரேக் பிடிக்கும்போது பெடல் தரை வரை இறங்குகிறது" },
    { label: "🔋 பேட்டரி டிக் டிக் சத்தம்", q: "சாவியை திருப்பும்போது டிக் டிக் சத்தம் மட்டும் கேட்கிறது வாகனம் ஸ்டார்ட் ஆகவில்லை" },
  ],
  te: [
    { label: "🔥 ఇంజిన్ వేడెక్కుతోంది", q: "ఇంజిన్ తీవ్రంగా వేడెక్కుతోంది మరియు కూలెంట్ ఉడుకుతోంది" },
    { label: "🛑 బ్రేక్ పెడల్ కిందకు దిగుతోంది", q: "బ్రేక్ వేసినప్పుడు పెడల్ కిందకు దిగిపోతోంది" },
    { label: "🔋 బ్యాటరీ డిశ్చార్జ్", q: "కీ తిప్పినప్పుడు క్లిక్ శబ్దం మాత్రమే వస్తోంది కారు స్టార్ట్ అవ్వడం లేదు" },
  ],
};

function renderMultilingualChips(langCode) {
  const container = document.getElementById("assistant-quick-chips");
  const input = document.getElementById("assistant-input");
  const form = document.getElementById("assistant-chat-form");
  if (!container) return;

  const list = MULTILINGUAL_EXAMPLE_CHIPS[langCode] || MULTILINGUAL_EXAMPLE_CHIPS.en;
  container.innerHTML = `
    <span style="font-size: 0.72rem; color: var(--text-dim);">Examples:</span>
    ${list.map((item) => `
      <button type="button" class="chip assist-chip" data-q="${item.q}">${item.label}</button>
    `).join("")}
  `;

  container.querySelectorAll(".assist-chip").forEach((btn) => {
    btn.addEventListener("click", () => {
      if (input) {
        input.value = btn.dataset.q;
        if (form) form.dispatchEvent(new Event("submit"));
      }
    });
  });
}

// ==========================================================================
// 2. Multilingual (i18n) Engine & Theme
// ==========================================================================
function initI18nAndLanguage() {
  const topLangSelect = document.getElementById("language-selector");
  const settingsLangSelect = document.getElementById("settings-lang-select");

  const syncLang = (langCode) => {
    if (window.i18n) {
      window.i18n.setLanguage(langCode);
    }
    if (topLangSelect) topLangSelect.value = langCode;
    if (settingsLangSelect) settingsLangSelect.value = langCode;
    if (window.voiceManager) {
      window.voiceManager.updateLanguage(langCode);
    }
    renderMultilingualChips(langCode);
  };

  if (topLangSelect) {
    topLangSelect.addEventListener("change", (e) => syncLang(e.target.value));
  }
  if (settingsLangSelect) {
    settingsLangSelect.addEventListener("change", (e) => syncLang(e.target.value));
  }

  // Load saved language
  const savedLang = localStorage.getItem("autoassist_lang") || "en";
  syncLang(savedLang);
}

function initTheme() {
  const themeBtn = document.getElementById("theme-toggle-btn");
  if (!themeBtn) return;

  const savedTheme = localStorage.getItem("autoassist_theme") || "dark";
  if (savedTheme === "light") {
    document.body.classList.add("light-theme");
    themeBtn.innerHTML = "🌙 Dark Mode";
  }

  themeBtn.addEventListener("click", () => {
    const isLight = document.body.classList.toggle("light-theme");
    localStorage.setItem("autoassist_theme", isLight ? "light" : "dark");
    themeBtn.innerHTML = isLight ? "🌙 Dark Mode" : "☀️ Light Mode";
  });
}

// ==========================================================================
// 3. Voice Controls (Speech-to-Text & Text-to-Speech)
// ==========================================================================
function initVoiceControls() {
  // Global Voice Output Toggle in Header
  const voiceToggleBtn = document.getElementById("header-voice-toggle");
  if (voiceToggleBtn && window.voiceManager) {
    const updateVoiceBtn = () => {
      const enabled = window.voiceManager.voiceOutputEnabled;
      voiceToggleBtn.innerHTML = enabled ? "🔊 Voice ON" : "🔇 Voice OFF";
      voiceToggleBtn.style.opacity = enabled ? "1" : "0.6";
    };
    updateVoiceBtn();

    voiceToggleBtn.addEventListener("click", () => {
      const current = window.voiceManager.voiceOutputEnabled;
      window.voiceManager.toggleVoiceOutput(!current);
      updateVoiceBtn();
    });
  }

  // Wire Microphone Buttons
  setupMicButton("assistant-mic-btn", "assistant-input");
  setupMicButton("manuals-mic-btn", "manual-search-input");
  setupMicButton("est-mic-btn", "est-query-input");
}

function setupMicButton(btnId, targetInputId) {
  const btn = document.getElementById(btnId);
  const input = document.getElementById(targetInputId);
  if (!btn || !input) return;

  btn.addEventListener("click", () => {
    if (!window.voiceManager) {
      alert("Voice engine not initialized.");
      return;
    }

    if (window.voiceManager.isRecording) {
      window.voiceManager.stopListening();
      btn.classList.remove("recording");
      btn.innerHTML = "🎤";
    } else {
      window.voiceManager.startListening(input, (isRec, status) => {
        if (isRec) {
          btn.classList.add("recording");
          btn.innerHTML = "⏹️";
        } else {
          btn.classList.remove("recording");
          btn.innerHTML = "🎤";
        }
      });
    }
  });
}

function setupVoicePlayerBar(barId, statusId, playId, pauseId, stopId, getTextToSpeak) {
  const bar = document.getElementById(barId);
  const statusElem = document.getElementById(statusId);
  const playBtn = document.getElementById(playId);
  const pauseBtn = document.getElementById(pauseId);
  const stopBtn = document.getElementById(stopId);

  if (!bar) return;

  if (playBtn) {
    playBtn.addEventListener("click", () => {
      if (!window.voiceManager) return;
      if (window.voiceManager.isPaused) {
        window.voiceManager.resume();
        if (statusElem) statusElem.innerText = "Speaking explanation...";
      } else {
        const text = getTextToSpeak();
        if (text) {
          const currentLang = (window.i18n && window.i18n.currentLang) || "en";
          window.voiceManager.speak(text, currentLang, (state) => {
            if (statusElem) {
              if (state === "loading") statusElem.innerText = "⏳ Buffering audio...";
              else if (state === "start" || state === "playing") statusElem.innerText = "🔊 Speaking explanation...";
              else if (state === "end" || state === "stopped") statusElem.innerText = "Playback completed";
              else if (state === "pause" || state === "paused") statusElem.innerText = "Playback paused";
              else if (state === "resume") statusElem.innerText = "🔊 Speaking explanation...";
              else if (state === "error") statusElem.innerText = "⚠️ Audio playback error";
            }
          });
        }
      }
    });
  }

  if (pauseBtn) {
    pauseBtn.addEventListener("click", () => {
      if (window.voiceManager) {
        window.voiceManager.pause();
        if (statusElem) statusElem.innerText = "Playback paused";
      }
    });
  }

  if (stopBtn) {
    stopBtn.addEventListener("click", () => {
      if (window.voiceManager) {
        window.voiceManager.stopSpeaking();
        if (statusElem) statusElem.innerText = "Playback stopped";
      }
    });
  }
}

// ==========================================================================
// 4. Vehicle Profile Management (/api/vehicles)
// ==========================================================================
function initVehiclesModule() {
  const addBtn = document.getElementById("add-vehicle-btn");
  const modal = document.getElementById("vehicle-modal");
  const closeBtn = document.getElementById("vehicle-modal-close");
  const form = document.getElementById("vehicle-form");

  if (addBtn && modal) {
    addBtn.addEventListener("click", () => {
      document.getElementById("vehicle-modal-title").innerText = "Add Vehicle Profile";
      document.getElementById("veh-form-id").value = "";
      document.getElementById("veh-form-make").value = "";
      document.getElementById("veh-form-model").value = "";
      document.getElementById("veh-form-year").value = "2022";
      document.getElementById("veh-form-mileage").value = "45000";
      document.getElementById("veh-form-city").value = "Bengaluru";
      document.getElementById("veh-form-default").checked = true;
      modal.classList.add("open");
    });
  }

  if (closeBtn && modal) {
    closeBtn.addEventListener("click", () => modal.classList.remove("open"));
  }

  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const vehId = document.getElementById("veh-form-id").value;
      const odo = parseInt(document.getElementById("veh-form-mileage").value, 10) || 45000;
      const city = document.getElementById("veh-form-city").value.trim() || "Bengaluru";
      const payload = {
        make: document.getElementById("veh-form-make").value.trim(),
        model: document.getElementById("veh-form-model").value.trim(),
        year: parseInt(document.getElementById("veh-form-year").value, 10),
        fuel_type: document.getElementById("veh-form-fuel").value,
        odometer: odo,
        mileage_km: odo,
        city: city,
        is_default: document.getElementById("veh-form-default").checked,
      };

      try {
        let resp;
        if (vehId) {
          resp = await fetch(`/api/vehicles/${vehId}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
          });
        } else {
          resp = await fetch("/api/vehicles", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
          });
        }

        if (!resp.ok) {
          const errData = await resp.json().catch(() => ({}));
          throw new Error(errData.detail || `Server returned error (${resp.status})`);
        }
        modal.classList.remove("open");
        await loadVehicles();
      } catch (err) {
        alert("Error saving vehicle profile: " + err.message);
      }
    });
  }
}

async function loadVehicles() {
  try {
    const resp = await fetch("/api/vehicles");
    if (!resp.ok) return;
    const list = await resp.json();
    state.vehiclesList = list;

    // Determine active default vehicle
    const active = list.find((v) => v.is_default) || list[0];
    if (active) {
      state.activeVehicle = active;
      updateActiveVehicleUI(active);
    }

    renderVehiclesGrid(list);
  } catch (err) {
    console.warn("Could not load vehicles:", err);
  }
}

function updateActiveVehicleUI(v) {
  const headerVeh = document.getElementById("header-vehicle-name");
  const dashVeh = document.getElementById("dash-metric-vehicle");
  const dashOdo = document.getElementById("dash-metric-odo");

  const odo = v.odometer || v.mileage_km || 45000;
  const city = v.city || (v.metadata && v.metadata.city) || "Bengaluru";

  if (headerVeh) headerVeh.innerText = `${v.make} ${v.model} (${v.year})`;
  if (dashVeh) dashVeh.innerText = `${v.make} ${v.model}`;
  if (dashOdo) dashOdo.innerText = `${odo.toLocaleString()} km • ${v.year} ${v.fuel_type || "Petrol"}`;

  // Sync with Cost Estimator inputs
  const estMake = document.getElementById("est-make");
  const estModel = document.getElementById("est-model");
  const estYear = document.getElementById("est-year");
  const estCity = document.getElementById("est-city");
  if (estMake && v.make) estMake.value = v.make;
  if (estModel && v.model) estModel.value = v.model;
  if (estYear && v.year) estYear.value = v.year;
  if (estCity && city) estCity.value = city;
}

function renderVehiclesGrid(vehicles) {
  const grid = document.getElementById("vehicles-grid");
  if (!grid) return;

  if (!vehicles || vehicles.length === 0) {
    grid.innerHTML = `
      <div style="grid-column: 1 / -1; padding: 2rem; text-align: center; color: var(--text-muted);">
        No vehicle profiles added yet. Click "+ Add New Vehicle" above to register your car.
      </div>
    `;
    return;
  }

  grid.innerHTML = vehicles
    .map(
      (v) => {
        const odo = v.odometer || v.mileage_km || 0;
        const city = v.city || (v.metadata && v.metadata.city) || "Bengaluru";
        return `
    <div class="vehicle-card ${v.is_default ? "is-default" : ""}">
      ${v.is_default ? `<span class="vehicle-card-badge">★ Active Vehicle</span>` : ""}
      <h3 style="font-size: 1.15rem; font-weight: 800; color: var(--text-main); margin-bottom: 0.35rem;">
        ${v.make} ${v.model}
      </h3>
      <div style="font-size: 0.82rem; color: var(--accent-cyan); margin-bottom: 0.75rem;">
        ${v.year} &bull; ${v.fuel_type || "Petrol"} &bull; ${odo.toLocaleString()} km
      </div>
      <div style="font-size: 0.78rem; color: var(--text-dim); margin-bottom: 1.25rem;">
        Location: <strong>${city}</strong>
      </div>
      <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
        ${
          !v.is_default
            ? `<button class="btn-icon" onclick="setActiveVehicle('${v.id}')" style="font-size: 0.75rem; color: var(--accent-cyan);">Set as Active</button>`
            : ""
        }
        <button class="btn-icon" onclick="editVehicle('${v.id}')" style="font-size: 0.75rem;">Edit</button>
        <button class="btn-icon" onclick="deleteVehicle('${v.id}')" style="font-size: 0.75rem; color: #fca5a5;">Delete</button>
      </div>
    </div>
  `;
      }
    )
    .join("");
}

window.setActiveVehicle = async function (vehId) {
  try {
    const resp = await fetch(`/api/vehicles/${vehId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ is_default: true }),
    });
    if (resp.ok) {
      await loadVehicles();
      loadMaintenanceOverview();
    }
  } catch (err) {
    alert("Could not set active vehicle: " + err.message);
  }
};

window.editVehicle = function (vehId) {
  const v = state.vehiclesList.find((item) => item.id === vehId);
  if (!v) return;

  const modal = document.getElementById("vehicle-modal");
  document.getElementById("vehicle-modal-title").innerText = "Edit Vehicle Profile";
  document.getElementById("veh-form-id").value = v.id;
  document.getElementById("veh-form-make").value = v.make || "";
  document.getElementById("veh-form-model").value = v.model || "";
  document.getElementById("veh-form-year").value = v.year || 2022;
  document.getElementById("veh-form-fuel").value = v.fuel_type || "Petrol";
  document.getElementById("veh-form-mileage").value = v.odometer || v.mileage_km || 45000;
  document.getElementById("veh-form-city").value = v.city || (v.metadata && v.metadata.city) || "Bengaluru";
  document.getElementById("veh-form-default").checked = !!v.is_default;
  if (modal) modal.classList.add("open");
};

window.deleteVehicle = async function (vehId) {
  if (!confirm("Are you sure you want to delete this vehicle profile?")) return;
  try {
    const resp = await fetch(`/api/vehicles/${vehId}`, { method: "DELETE" });
    if (resp.ok) await loadVehicles();
  } catch (err) {
    alert("Could not delete vehicle: " + err.message);
  }
};

// ==========================================================================
// 5. Maintenance Tracker Module (/api/maintenance)
// ==========================================================================
function initMaintenanceModule() {}

async function loadMaintenanceOverview() {
  const tbody = document.getElementById("maintenance-tbody");
  const summaryText = document.getElementById("maint-summary-text");
  const dashCount = document.getElementById("dash-metric-maint-count");

  try {
    const v = state.activeVehicle;
    const url = `/api/maintenance/overview?vehicle_id=${v.id || ""}&current_mileage=${v.mileage_km || 45000}`;
    const resp = await fetch(url);
    if (!resp.ok) return;

    const data = await resp.json();
    const items = data.records || data.items || [];

    // Update alert counts
    const overdueCount = items.filter((i) => i.status === "overdue").length;
    const dueSoonCount = items.filter((i) => i.status === "due_soon").length;

    if (summaryText) {
      if (overdueCount > 0) {
        summaryText.innerHTML = `<span style="color: #fca5a5;">${overdueCount} Overdue Service(s)</span>`;
      } else if (dueSoonCount > 0) {
        summaryText.innerHTML = `<span style="color: #fcd34d;">${dueSoonCount} Due Soon</span>`;
      } else {
        summaryText.innerHTML = `<span style="color: #6ee7b7;">All Systems Up-to-Date</span>`;
      }
    }

    if (dashCount) {
      if (overdueCount > 0) {
        dashCount.innerText = `${overdueCount} Overdue`;
        dashCount.style.color = "var(--accent-crimson)";
      } else if (dueSoonCount > 0) {
        dashCount.innerText = `${dueSoonCount} Due Soon`;
        dashCount.style.color = "var(--accent-amber)";
      } else {
        dashCount.innerText = "Up-to-Date";
        dashCount.style.color = "var(--accent-emerald)";
      }
    }

    if (tbody) {
      tbody.innerHTML = items
        .map(
          (item) => `
        <tr>
          <td style="font-weight: 700; color: var(--text-main);">
            ${item.service_type || item.service_name || "Scheduled Maintenance"}
            <div style="font-size: 0.72rem; color: var(--text-dim); font-weight: normal;">${item.notes || ""}</div>
          </td>
          <td style="font-size: 0.78rem; color: var(--text-muted);">${item.interval_km ? `${item.interval_km.toLocaleString()} km` : ""}${item.interval_months ? ` / ${item.interval_months} mo` : ""}</td>
          <td style="font-size: 0.78rem;">${item.last_service_date || item.last_performed_date || "Not recorded"}<br><span style="color: var(--text-dim);">${item.last_service_odometer ? `${item.last_service_odometer.toLocaleString()} km` : ""}</span></td>
          <td style="font-size: 0.78rem; color: var(--accent-cyan); font-weight: 600;">${item.next_due_date || ""}<br><span>${item.next_due_odometer ? `${item.next_due_odometer.toLocaleString()} km` : ""}</span></td>
          <td><span class="maint-status-pill ${item.status}">${item.status.replace("_", " ")}</span></td>
          <td>
            <button class="btn-icon" onclick="completeMaintenance('${item.id}', '${item.service_type || item.service_name}')" style="font-size: 0.72rem; color: var(--accent-emerald);">
              ✓ Mark Done
            </button>
          </td>
        </tr>
      `
        )
        .join("");
    }
  } catch (err) {
    console.warn("Could not load maintenance overview:", err);
  }
}

window.completeMaintenance = async function (recordId, serviceName) {
  const currentOdo = state.activeVehicle.mileage_km || 45000;
  const odo = prompt(`Enter service odometer for "${serviceName}":`, currentOdo);
  if (odo === null) return;

  try {
    const resp = await fetch(`/api/maintenance/records/${recordId}/complete`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        mileage: parseInt(odo, 10) || currentOdo,
        notes: "Completed via AutoAssist AI web portal",
      }),
    });
    if (resp.ok) {
      await loadMaintenanceOverview();
    }
  } catch (err) {
    alert("Could not mark maintenance complete: " + err.message);
  }
};

// ==========================================================================
// 6. AI Assistant & Severity Assessment (/api/severity/assess & /api/rag/explain)
// ==========================================================================
function initAssistantChat() {
  const form = document.getElementById("assistant-chat-form");
  const input = document.getElementById("assistant-input");
  const chips = document.querySelectorAll(".assist-chip");
  const severityContainer = document.getElementById("assistant-severity-container");
  const resultContainer = document.getElementById("assistant-result-container");

  chips.forEach((c) => {
    c.addEventListener("click", () => {
      if (input) {
        input.value = c.dataset.q;
        form.dispatchEvent(new Event("submit"));
      }
    });
  });

  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const query = input.value.trim();
    if (!query) return;

    if (resultContainer) {
      resultContainer.innerHTML = `
        <div style="padding: 2rem; text-align: center; color: var(--accent-cyan);">
          <div class="status-dot" style="margin: 0 auto 0.75rem; width: 12px; height: 12px;"></div>
          Consulting 129 OEM service manual sections & calculating severity risk...
        </div>
      `;
    }

    try {
      // 1. Run Severity Assessment in parallel with RAG explanation
      const [sevResp, ragResp] = await Promise.all([
        fetch("/api/severity/assess", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ query: query }),
        }),
        fetch("/api/rag/explain", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            query: query,
            top_k: 4,
            language: (window.i18n && window.i18n.currentLang) || "en",
          }),
        }),
      ]);

      const sevData = await sevResp.json();
      const ragData = await ragResp.json();

      // Render Severity Banner
      if (severityContainer) {
        severityContainer.style.display = "block";
        const sevClass = sevData.severity === "CRITICAL" ? "severity-critical" : sevData.severity === "MODERATE" ? "severity-moderate" : "severity-low";
        const sevIcon = sevData.severity === "CRITICAL" ? "🛑" : sevData.severity === "MODERATE" ? "⚠️" : "ℹ️";

        severityContainer.innerHTML = `
          <div class="severity-banner ${sevClass}">
            <span style="font-size: 1.5rem;">${sevIcon}</span>
            <div>
              <div class="severity-title">${sevData.severity} SEVERITY HAZARD</div>
              <div>${sevData.rationale}</div>
              ${
                sevData.stop_driving_immediately
                  ? `<div style="font-weight: 800; color: #ffffff; margin-top: 0.35rem; background: #dc2626; padding: 0.3rem 0.6rem; border-radius: 4px; display: inline-block;">⚠️ DO NOT DRIVE: Pull over safely and arrange towing.</div>`
                  : ""
              }
            </div>
          </div>
        `;
      }

      // Render RAG Explanation
      state.manualResult = ragData;
      renderAssistantResult(ragData, resultContainer);

      // Automatically speak explanation when query is taken and analyzed
      if (window.voiceManager && ragData.simple_explanation) {
        const autoVoice = document.getElementById("settings-auto-voice");
        const isAutoEnabled = !autoVoice || autoVoice.checked;
        if (isAutoEnabled) {
          setTimeout(() => {
            speakCurrentAssistantResult();
          }, 150);
        }
      }
    } catch (err) {
      if (resultContainer) {
        resultContainer.innerHTML = `
          <div style="padding: 1.5rem; background: rgba(239, 68, 68, 0.1); border: 1px solid var(--accent-crimson); border-radius: 8px; color: #fca5a5;">
            <strong>Analysis Error:</strong> ${err.message}. Please verify the backend is running.
          </div>
        `;
      }
    }
  });
}

function formatListOrStr(val, fallback = "") {
  if (!val) return fallback;
  if (Array.isArray(val)) {
    return `<ul style="padding-left: 1.25rem; margin: 0.25rem 0;">${val.map((item) => `<li>${item}</li>`).join("")}</ul>`;
  }
  return val;
}

function renderAssistantResult(data, container) {
  if (!container) return;
  const exp = data.simple_explanation || {};
  const questions = data.questions_for_mechanic || exp.suggested_mechanic_questions || [];

  container.innerHTML = `
    <div class="simple-explanation-card">
      <div class="simple-section-block">
        <div class="simple-sec-title">💡 What does it mean?</div>
        <div class="simple-sec-body">${exp.what_does_it_mean || "No explanation available."}</div>
      </div>

      <div class="simple-section-block">
        <div class="simple-sec-title">🔍 Why does it happen?</div>
        <div class="simple-sec-body">${exp.why_does_it_happen || "Information not found."}</div>
      </div>

      <div class="simple-section-block">
        <div class="simple-sec-title">⚠️ What symptoms might you notice?</div>
        <div class="simple-sec-body">${formatListOrStr(exp.symptoms_you_might_notice || exp.what_symptoms_might_you_notice, "None specified.")}</div>
      </div>

      <div class="simple-section-block">
        <div class="simple-sec-title">✅ What should you do?</div>
        <div class="simple-sec-body">${formatListOrStr(exp.what_should_you_do, "Follow vehicle safety guidelines.")}</div>
      </div>

      <div class="simple-section-block">
        <div class="simple-sec-title">🔧 When should you visit a mechanic?</div>
        <div class="simple-sec-body">${exp.when_to_visit_mechanic || "If symptoms persist."}</div>
      </div>

      ${
        questions.length > 0
          ? `
        <div class="ask-mechanic-box">
          <div class="ask-mechanic-header">
            <h4 style="font-size: 0.9rem; font-weight: 700; color: var(--accent-cyan);">🗣️ Recommended Questions for Your Mechanic:</h4>
            <button type="button" class="btn-icon" onclick="copyQuestionsToClipboard()" style="font-size: 0.72rem;">📋 Copy</button>
          </div>
          <ul class="ask-mechanic-list" id="assist-questions-list">
            ${questions.map((q) => `<li>${q}</li>`).join("")}
          </ul>
        </div>
      `
          : ""
      }

      <div class="voice-player-bar">
        <div style="display: flex; align-items: center; gap: 0.5rem;">
          <span>🔊</span>
          <span id="assist-voice-status" style="font-size: 0.8rem; font-weight: 600;">Listen to AI explanation</span>
        </div>
        <div class="voice-btn-group">
          <button type="button" class="voice-btn" onclick="speakCurrentAssistantResult()">▶️ Play</button>
          <button type="button" class="voice-btn" onclick="window.voiceManager?.pause()">⏸️ Pause</button>
          <button type="button" class="voice-btn" onclick="window.voiceManager?.stopSpeaking()">⏹️ Stop</button>
        </div>
      </div>
    </div>
  `;
}

window.speakCurrentAssistantResult = function () {
  if (!window.voiceManager || !state.manualResult || !state.manualResult.simple_explanation) return;
  const exp = state.manualResult.simple_explanation;
  const currentLang = (window.i18n && window.i18n.currentLang) || "en";
  const statusElem = document.getElementById("assist-voice-status");
  const parts = [];
  if (exp.what_does_it_mean) parts.push(exp.what_does_it_mean);
  if (exp.why_does_it_happen) parts.push(exp.why_does_it_happen);
  if (Array.isArray(exp.what_should_you_do)) {
    parts.push(exp.what_should_you_do.join(". "));
  } else if (exp.what_should_you_do) {
    parts.push(exp.what_should_you_do);
  }
  const text = parts.join(" ");
  const langLabel = (window.voiceManager.langNames && window.voiceManager.langNames[currentLang]) || currentLang;
  window.voiceManager.speak(text, currentLang, (state) => {
    if (statusElem) {
      if (state === "loading") statusElem.innerText = "⏳ Buffering audio in " + langLabel + "...";
      else if (state === "start" || state === "playing") statusElem.innerText = "🔊 Speaking in " + langLabel + "...";
      else if (state === "end" || state === "stopped") statusElem.innerText = "Playback completed";
      else if (state === "pause" || state === "paused") statusElem.innerText = "Playback paused";
      else if (state === "error") statusElem.innerText = "⚠️ Audio playback error";
    }
  });
};

// ==========================================================================
// 7. Intelligent Manual Search with Dual View (/api/rag/explain)
// ==========================================================================
function initManualsSearch() {
  const form = document.getElementById("manuals-search-form");
  const input = document.getElementById("manual-search-input");
  const chips = document.querySelectorAll(".manual-chip");

  chips.forEach((c) => {
    c.addEventListener("click", () => {
      if (input) {
        input.value = c.dataset.q;
        form.dispatchEvent(new Event("submit"));
      }
    });
  });

  setupVoicePlayerBar(
    "manual-voice-bar",
    "manual-voice-status",
    "manual-voice-play",
    "manual-voice-pause",
    "manual-voice-stop",
    () => {
      if (!state.manualResult || !state.manualResult.simple_explanation) return "";
      const exp = state.manualResult.simple_explanation;
      return `${exp.what_does_it_mean} ${exp.what_should_you_do}`;
    }
  );

  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const query = input.value.trim();
    if (!query) return;

    const container = document.getElementById("manuals-results-container");
    const voiceBar = document.getElementById("manual-voice-bar");
    if (container) {
      container.innerHTML = `
        <div style="padding: 2.5rem; text-align: center; color: var(--accent-cyan);">
          <div class="status-dot" style="margin: 0 auto 0.75rem; width: 14px; height: 14px;"></div>
          Dense ONNX 384d semantic retrieval across 9 factory OEM service manuals...
        </div>
      `;
    }

    try {
      const resp = await fetch("/api/rag/explain", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: query,
          top_k: 5,
          language: (window.i18n && window.i18n.currentLang) || "en",
        }),
      });

      if (!resp.ok) throw new Error(`Server returned HTTP ${resp.status}`);
      const data = await resp.json();
      state.manualResult = data;

      if (voiceBar) voiceBar.style.display = "flex";
      renderManualSearchResults();

      // Automatically speak explanation when manual query is taken
      if (window.voiceManager && data.simple_explanation) {
        const autoVoice = document.getElementById("settings-auto-voice");
        const isAutoEnabled = !autoVoice || autoVoice.checked;
        if (isAutoEnabled) {
          const playBtn = document.getElementById("manual-voice-play");
          if (playBtn) {
            setTimeout(() => playBtn.click(), 150);
          }
        }
      }
    } catch (err) {
      if (container) {
        container.innerHTML = `
          <div style="padding: 1.5rem; background: rgba(239, 68, 68, 0.1); border: 1px solid var(--accent-crimson); border-radius: 8px; color: #fca5a5;">
            <strong>Search Error:</strong> ${err.message}. Please verify the backend is running.
          </div>
        `;
      }
    }
  });
}

window.switchManualView = function (viewMode) {
  state.manualViewMode = viewMode;
  const simpleBtn = document.getElementById("btn-view-simple");
  const techBtn = document.getElementById("btn-view-technical");

  if (viewMode === "simple") {
    if (simpleBtn) simpleBtn.classList.add("active");
    if (techBtn) techBtn.classList.remove("active");
  } else {
    if (techBtn) techBtn.classList.add("active");
    if (simpleBtn) simpleBtn.classList.remove("active");
  }

  renderManualSearchResults();
};

function renderManualSearchResults() {
  const container = document.getElementById("manuals-results-container");
  if (!container || !state.manualResult) return;

  const data = state.manualResult;
  const isSimple = state.manualViewMode === "simple";

  if (isSimple) {
    const exp = data.simple_explanation || {};
    const questions = data.questions_for_mechanic || [];

    container.innerHTML = `
      <div class="simple-explanation-card">
        <div class="simple-section-block">
          <div class="simple-sec-title">💡 What does it mean?</div>
          <div class="simple-sec-body">${exp.what_does_it_mean || "Grounded explanation being processed."}</div>
        </div>

        <div class="simple-section-block">
          <div class="simple-sec-title">⚙️ Why does it happen?</div>
          <div class="simple-sec-body">${exp.why_does_it_happen || "Potential mechanical causes being referenced."}</div>
        </div>

        <div class="simple-section-block">
          <div class="simple-sec-title">⚠️ What symptoms might you notice?</div>
          <div class="simple-sec-body">${formatListOrStr(exp.symptoms_you_might_notice || exp.what_symptoms_might_you_notice, "Common observable signs.")}</div>
        </div>

        <div class="simple-section-block">
          <div class="simple-sec-title">🛡️ What should you do?</div>
          <div class="simple-sec-body">${formatListOrStr(exp.what_should_you_do, "Safe recommended actions.")}</div>
        </div>

        <div class="simple-section-block">
          <div class="simple-sec-title">👨‍🔧 When should you visit a mechanic?</div>
          <div class="simple-sec-body">${exp.when_to_visit_mechanic || "Professional inspection criteria."}</div>
        </div>

        ${
          questions.length > 0
            ? `
          <div class="ask-mechanic-box">
            <div class="ask-mechanic-header">
              <h4 style="font-size: 0.9rem; font-weight: 700; color: var(--accent-cyan);">🗣️ Recommended Questions for Your Mechanic:</h4>
              <button type="button" class="btn-icon" onclick="copyQuestionsToClipboard()" style="font-size: 0.72rem;">📋 Copy Questions</button>
            </div>
            <ul class="ask-mechanic-list" id="manual-questions-list">
              ${questions.map((q) => `<li>${q}</li>`).join("")}
            </ul>
          </div>
        `
            : ""
        }
      </div>
    `;
  } else {
    // Technical OEM Manual Passages View
    const chunks = data.technical_passages || [];
    container.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
        <span style="font-size: 0.85rem; color: var(--text-muted);">
          Retrieved <strong>${chunks.length}</strong> official OEM manual passages (Cosine similarity)
        </span>
        <span style="font-size: 0.75rem; color: var(--accent-cyan); font-family: monospace;">all-MiniLM-L6-v2 ONNX</span>
      </div>

      <div class="rag-chunks-list">
        ${chunks
          .map(
            (c, idx) => `
          <div class="rag-chunk-card" style="border-left-width: 4px;">
            <div class="rag-chunk-header">
              <div>
                <span style="background: rgba(56, 189, 248, 0.15); color: var(--accent-cyan); padding: 0.15rem 0.5rem; border-radius: 4px; font-size: 0.75rem; margin-right: 0.5rem;">#${idx + 1}</span>
                <strong>${c.document_title || "OEM Service Manual"}</strong>
                <span style="color: var(--text-dim); font-size: 0.75rem;"> &bull; Section: ${c.section || "Technical Procedure"} (Page ${c.page_number || 1})</span>
              </div>
              <div style="font-family: monospace; font-size: 0.8rem; color: var(--accent-cyan);">
                Sim: ${(c.similarity || 0.85).toFixed(4)}
              </div>
            </div>
            <div class="rag-chunk-text" style="font-size: 0.85rem; margin-top: 0.6rem; line-height: 1.6;">${c.content}</div>
          </div>
        `
          )
          .join("")}
      </div>
    `;
  }
}

window.copyQuestionsToClipboard = function () {
  const list = document.querySelectorAll(".ask-mechanic-list li");
  const text = Array.from(list)
    .map((li, idx) => `${idx + 1}. ${li.innerText}`)
    .join("\n");
  navigator.clipboard.writeText(text).then(() => {
    alert("Mechanic questions copied to clipboard!");
  });
};

// ==========================================================================
// 8. AI Repair Cost Estimator (/api/pricing/estimate)
// ==========================================================================
function initCostEstimator() {
  const form = document.getElementById("estimator-form");
  const input = document.getElementById("est-query-input");
  const chips = document.querySelectorAll(".est-chip");
  const container = document.getElementById("estimator-result-container");

  chips.forEach((c) => {
    c.addEventListener("click", () => {
      if (input) {
        input.value = c.dataset.q;
        form.dispatchEvent(new Event("submit"));
      }
    });
  });

  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const query = input.value.trim();
    if (!query) return;

    if (container) {
      container.innerHTML = `
        <div style="padding: 2.5rem; text-align: center; color: var(--accent-cyan);">
          <div class="status-dot" style="margin: 0 auto 0.75rem; width: 14px; height: 14px;"></div>
          Querying verified spare parts and local labor rate database...
        </div>
      `;
    }

    const payload = {
      problem_query: query,
      vehicle_make: document.getElementById("est-make")?.value || state.activeVehicle.make,
      vehicle_model: document.getElementById("est-model")?.value || state.activeVehicle.model,
      vehicle_year: parseInt(document.getElementById("est-year")?.value || "2022", 10),
      city: document.getElementById("est-city")?.value || "Bengaluru",
    };

    try {
      const resp = await fetch("/api/pricing/estimate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!resp.ok) throw new Error(`Server returned HTTP ${resp.status}`);
      const data = await resp.json();
      renderCostEstimateResult(data, container);
    } catch (err) {
      if (container) {
        container.innerHTML = `
          <div style="padding: 1.5rem; background: rgba(239, 68, 68, 0.1); border: 1px solid var(--accent-crimson); border-radius: 8px; color: #fca5a5;">
            <strong>Estimator Error:</strong> ${err.message}. Please verify the backend is running.
          </div>
        `;
      }
    }
  });
}

function renderCostEstimateResult(data, container) {
  if (!container) return;

  if (!data.matched) {
    container.innerHTML = `
      <div style="padding: 1.75rem; background: rgba(148, 163, 184, 0.08); border: 1px solid var(--border-color); border-radius: var(--radius-md); text-align: center;">
        <span style="font-size: 2rem;">🔍</span>
        <h3 style="font-size: 1.1rem; font-weight: 700; color: var(--text-main); margin: 0.5rem 0;">Pricing data unavailable</h3>
        <p style="font-size: 0.85rem; color: var(--text-muted); max-width: 500px; margin: 0 auto 0.75rem;">
          No verified OEM spare-part or labor record matched "${data.query || "this component"}". AutoAssist AI strictly avoids generating fabricated or imaginary prices.
        </p>
        <div style="font-size: 0.75rem; color: var(--text-dim);">
          Tip: Try searching for a specific component such as "Brake Pads", "Alternator", "Thermostat", or "Engine Oil".
        </div>
      </div>
    `;
    return;
  }

  container.innerHTML = `
    <div style="background: var(--bg-card); border: 1px solid var(--border-color); border-radius: var(--radius-lg); padding: 1.5rem;">
      <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255, 255, 255, 0.06); padding-bottom: 1rem; margin-bottom: 1.25rem;">
        <div>
          <span style="font-size: 0.72rem; text-transform: uppercase; color: var(--accent-cyan); font-weight: 700; letter-spacing: 0.5px;">Verified Cost Breakdown &bull; ${data.currency || "INR"}</span>
          <h3 style="font-size: 1.25rem; font-weight: 800; color: var(--text-main); margin-top: 0.2rem;">${data.part_name}</h3>
          <span style="font-size: 0.78rem; color: var(--text-muted);">${data.vehicle_applied || "All Vehicles"} &bull; Category: ${data.category || "Mechanical"}</span>
        </div>
        <div style="text-align: right;">
          <span style="font-size: 0.75rem; color: var(--text-dim);">Location Labor Modifier:</span>
          <div style="font-weight: 700; color: var(--accent-cyan);">${data.city_applied || "All India"}</div>
        </div>
      </div>

      <div class="dashboard-metrics-grid" style="margin-bottom: 1.25rem;">
        <div class="metric-card">
          <span class="metric-label">Spare Parts Range</span>
          <span class="metric-val" style="color: var(--accent-cyan); font-size: 1.35rem;">${data.parts_cost_range_inr}</span>
        </div>
        <div class="metric-card">
          <span class="metric-label">Estimated Labor</span>
          <span class="metric-val" style="color: var(--accent-amber); font-size: 1.35rem;">${data.labor_hours} hrs</span>
          <span style="font-size: 0.75rem; color: var(--text-dim); margin-top: 0.25rem;">${data.labor_charge_inr}</span>
        </div>
        <div class="metric-card">
          <span class="metric-label">Total Estimated Repair</span>
          <span class="metric-val" style="color: var(--accent-emerald); font-size: 1.35rem;">${data.total_estimated_cost_inr}</span>
        </div>
      </div>

      <div style="overflow-x: auto; margin-bottom: 1rem;">
        <table class="quote-table">
          <thead>
            <tr>
              <th>Component / Service</th>
              <th>Part Price Range</th>
              <th>Labor Hours</th>
              <th>Labor Charge</th>
              <th>Skill Rating</th>
              <th>Pricing Source</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td style="font-weight: 700;">${data.part_name}</td>
              <td style="color: var(--accent-cyan);">${data.parts_cost_range_inr}</td>
              <td>${data.labor_hours} hrs</td>
              <td style="color: var(--accent-amber);">${data.labor_charge_inr}</td>
              <td><span class="badge-risk badge-MEDIUM" style="font-size: 0.7rem;">${data.difficulty || "Intermediate"}</span></td>
              <td style="font-size: 0.75rem; color: var(--text-dim);">${data.pricing_source || "Verified OEM Reference"}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div style="font-size: 0.74rem; color: var(--text-dim); line-height: 1.5; padding: 0.75rem; background: rgba(15, 23, 42, 0.6); border-radius: 6px;">
        ⚠️ <strong>Disclaimer:</strong> ${data.disclaimer}
      </div>
    </div>
  `;
}

// ==========================================================================
// 9. Mechanic Quotation Checker (/api/quotations/evaluate)
// ==========================================================================
function initQuotationChecker() {
  const addRowBtn = document.getElementById("quote-add-item-btn");
  const tbody = document.getElementById("quote-items-tbody");
  const form = document.getElementById("quote-checker-form");
  const container = document.getElementById("quote-results-container");

  if (addRowBtn && tbody) {
    addRowBtn.addEventListener("click", () => {
      const tr = document.createElement("tr");
      tr.className = "quote-input-row";
      tr.innerHTML = `
        <td><input type="text" class="text-input row-item-name" placeholder="e.g. Engine Oil Flush" required></td>
        <td><input type="number" class="text-input row-part-price" value="0" min="0" required></td>
        <td><input type="number" class="text-input row-labor-price" value="0" min="0" required></td>
        <td style="text-align: center;"><button type="button" class="btn-icon remove-row-btn" style="padding: 0.2rem 0.5rem; color: #fca5a5;">✕</button></td>
      `;
      tbody.appendChild(tr);
      attachRemoveRowListeners();
    });
  }

  attachRemoveRowListeners();

  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const rows = document.querySelectorAll("#quote-items-tbody .quote-input-row");
    const items = [];

    rows.forEach((row) => {
      const name = row.querySelector(".row-item-name")?.value.trim();
      const parts = parseFloat(row.querySelector(".row-part-price")?.value || "0");
      const labor = parseFloat(row.querySelector(".row-labor-price")?.value || "0");
      if (name) {
        items.push({
          item_name: name,
          quoted_part_price: parts,
          quoted_labor_price: labor,
        });
      }
    });

    if (items.length === 0) {
      alert("Please add at least one quotation item.");
      return;
    }

    if (container) {
      container.innerHTML = `
        <div style="padding: 2.5rem; text-align: center; color: var(--accent-cyan);">
          <div class="status-dot" style="margin: 0 auto 0.75rem; width: 14px; height: 14px;"></div>
          Cross-checking line items against verified regional benchmarks...
        </div>
      `;
    }

    const payload = {
      title: document.getElementById("quote-job-title")?.value || "Workshop Quotation",
      garage_name: document.getElementById("quote-garage-name")?.value || null,
      city: document.getElementById("quote-city")?.value || "Bengaluru",
      items: items,
    };

    try {
      const resp = await fetch("/api/quotations/evaluate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!resp.ok) throw new Error(`Server returned HTTP ${resp.status}`);
      const data = await resp.json();
      renderQuotationResults(data, container);
    } catch (err) {
      if (container) {
        container.innerHTML = `
          <div style="padding: 1.5rem; background: rgba(239, 68, 68, 0.1); border: 1px solid var(--accent-crimson); border-radius: 8px; color: #fca5a5;">
            <strong>Evaluation Error:</strong> ${err.message}. Please verify the backend is running.
          </div>
        `;
      }
    }
  });
}

function attachRemoveRowListeners() {
  const removeBtns = document.querySelectorAll(".remove-row-btn");
  removeBtns.forEach((b) => {
    b.onclick = function () {
      const row = b.closest("tr");
      if (document.querySelectorAll("#quote-items-tbody tr").length > 1) {
        row.remove();
      } else {
        alert("At least one quotation line item is required.");
      }
    };
  });
}

function renderQuotationResults(data, container) {
  if (!container) return;

  const statusBadge = (st) => {
    const s = (st || "").toLowerCase();
    if (s.includes("within")) return `<span class="quote-badge badge-within">Within Range</span>`;
    if (s.includes("above") || s.includes("higher")) return `<span class="quote-badge badge-above">Above Reference</span>`;
    if (s.includes("below") || s.includes("lower")) return `<span class="quote-badge badge-below">Below Reference</span>`;
    return `<span class="quote-badge badge-unavailable">No Data</span>`;
  };

  const title = data.repair_title || data.title || "Quotation Review";
  const totalQuoted = data.total_quoted || data.total_quoted_cost || 0;
  const refMin = data.total_reference_min || 0;
  const refMax = data.total_reference_max || 0;

  container.innerHTML = `
    <div style="background: var(--bg-card); border: 1px solid var(--border-color); border-radius: var(--radius-lg); padding: 1.5rem;">
      <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255, 255, 255, 0.06); padding-bottom: 1rem; margin-bottom: 1.25rem;">
        <div>
          <h3 style="font-size: 1.25rem; font-weight: 800; color: var(--text-main);">${title}</h3>
          <span style="font-size: 0.78rem; color: var(--text-muted);">${data.garage_name || "General Workshop"} &bull; City: ${data.city || "Bengaluru"}</span>
        </div>
        <div style="text-align: right;">
          <span style="font-size: 0.72rem; color: var(--text-dim); text-transform: uppercase;">Total Quoted vs Benchmark</span>
          <div style="font-size: 1.2rem; font-weight: 800; color: var(--accent-cyan);">
            ₹${totalQuoted.toLocaleString()} <span style="font-size: 0.8rem; color: var(--text-muted); font-weight: normal;">(Ref: ₹${refMin.toLocaleString()}–₹${refMax.toLocaleString()})</span>
          </div>
        </div>
      </div>

      <div class="quote-table-wrapper" style="margin-bottom: 1.25rem;">
        <table class="quote-table">
          <thead>
            <tr>
              <th>Line Item</th>
              <th>Quoted Total (₹)</th>
              <th>Verified Range (₹)</th>
              <th>Variance</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            ${(data.items || [])
              .map(
                (item) => `
              <tr>
                <td style="font-weight: 700;">
                  ${item.service_or_part || item.item_name || "Service Item"}
                  <div style="font-size: 0.72rem; color: var(--text-dim); font-weight: normal;">Parts: ₹${(item.quoted_part_price || 0).toLocaleString()} | Labor: ₹${(item.quoted_labor_price || 0).toLocaleString()}</div>
                </td>
                <td style="font-weight: 700; color: var(--text-main);">₹${(item.quoted_total || 0).toLocaleString()}</td>
                <td style="color: var(--accent-cyan);">${item.reference_range_display || (item.reference_total_min ? `₹${item.reference_total_min.toLocaleString()} – ₹${item.reference_total_max.toLocaleString()}` : "Unavailable")}</td>
                <td style="font-size: 0.8rem; color: ${(item.difference_max || 0) > 0 ? 'var(--accent-amber)' : 'var(--accent-emerald)'};">${(item.difference_max || 0) > 0 ? `+₹${item.difference_max.toLocaleString()}` : "₹0"}</td>
                <td>${statusBadge(item.status)}</td>
              </tr>
            `
              )
              .join("")}
          </tbody>
        </table>
      </div>

      <!-- Educational Note -->
      <div style="padding: 1rem; background: rgba(37, 99, 235, 0.08); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 8px; margin-bottom: 1.25rem;">
        <h4 style="font-size: 0.88rem; font-weight: 700; color: var(--accent-cyan); margin-bottom: 0.35rem;">💡 Educational Note on Price Differences:</h4>
        <p style="font-size: 0.82rem; color: var(--text-muted); line-height: 1.5;">${data.educational_note || "Prices can vary based on genuine OEM vs aftermarket components and technician expertise."}</p>
      </div>

      <!-- Mechanic Discussion Questions -->
      ${
        data.questions_for_mechanic && data.questions_for_mechanic.length > 0
          ? `
        <div class="ask-mechanic-box" style="margin-top: 0;">
          <div class="ask-mechanic-header">
            <h4 style="font-size: 0.88rem; font-weight: 700; color: var(--accent-cyan);">🗣️ Non-Confrontational Questions for Your Garage:</h4>
            <button type="button" class="btn-icon" onclick="copyQuestionsToClipboard()" style="font-size: 0.72rem;">📋 Copy Questions</button>
          </div>
          <ul class="ask-mechanic-list">
            ${data.questions_for_mechanic.map((q) => `<li>${q}</li>`).join("")}
          </ul>
        </div>
      `
          : ""
      }
    </div>
  `;
}

// ==========================================================================
// 10. Settings & Preferences Panel
// ==========================================================================
function initSettingsPanel() {
  const rateSlider = document.getElementById("settings-voice-rate");
  const pitchSlider = document.getElementById("settings-voice-pitch");
  const rateVal = document.getElementById("voice-rate-val");
  const pitchVal = document.getElementById("voice-pitch-val");
  const voiceSelect = document.getElementById("settings-voice-select");
  const testVoiceBtn = document.getElementById("settings-test-voice-btn");

  if (rateSlider && rateVal && window.voiceManager) {
    rateSlider.value = window.voiceManager.speechRate;
    rateVal.innerText = `${rateSlider.value}x`;
    rateSlider.addEventListener("input", () => {
      rateVal.innerText = `${rateSlider.value}x`;
      window.voiceManager.setSpeechRate(parseFloat(rateSlider.value));
    });
  }

  if (pitchSlider && pitchVal && window.voiceManager) {
    pitchSlider.value = window.voiceManager.speechPitch;
    pitchVal.innerText = pitchSlider.value;
    pitchSlider.addEventListener("input", () => {
      pitchVal.innerText = pitchSlider.value;
      window.voiceManager.setSpeechPitch(parseFloat(pitchSlider.value));
    });
  }

  if (voiceSelect && window.voiceManager) {
    voiceSelect.addEventListener("change", () => {
      window.voiceManager.setVoiceURI(voiceSelect.value);
    });
  }

  if (testVoiceBtn && window.voiceManager) {
    testVoiceBtn.addEventListener("click", () => {
      const lang = (window.i18n && window.i18n.currentLang) || "en";
      const sampleTexts = {
        en: "AutoAssist AI voice synthesis online. Engine diagnostic telemetry verified.",
        kn: "ಆಟೋಅಸಿಸ್ಟ್ ಎಐ ಧ್ವನಿ ಸಿದ್ಧವಾಗಿದೆ. ವಾಹನ ತಪಾಸಣೆ ಪರಿಶೀಲಿಸಲಾಗಿದೆ.",
        hi: "ऑटोअसिस्ट एआई आवाज़ संश्लेषण तैयार है। आपका वाहन डायग्नोस्टिक सत्यापित है।",
        ur: "آٹو اسسٹ اے آئی آواز فعال ہے۔ گاڑی کی تشخیص کی تصدیق ہو چکی ہے۔",
        ml: "ഓട്ടോഅസിസ്റ്റ് എഐ ശബ്ദ സംവിധാനം സജ്ജമാണ്. വാഹന പരിശോധന സ്ഥിരീകരിച്ചു.",
        ta: "ஆட்டோஅசிஸ்ட் ஏஐ குரல் முறைமை தயார். வாகன கண்டறிதல் சரிபார்க்கப்பட்டது.",
        te: "ఆటోఅసిస్ట్ AI వాయిస్ సిస్టమ్ సిద్ధంగా ఉంది. వాహన డయాగ్నస్టిక్ ధృవీకరించబడింది.",
      };
      const origText = testVoiceBtn.innerHTML;
      testVoiceBtn.innerHTML = "⏳ Buffering...";
      window.voiceManager.speak(sampleTexts[lang] || sampleTexts.en, lang, (state) => {
        if (state === "start" || state === "playing") {
          testVoiceBtn.innerHTML = "🔊 Speaking...";
        } else if (state === "end" || state === "stopped" || state === "error") {
          testVoiceBtn.innerHTML = origText;
        }
      });
    });
  }
}

window.startQuickVoiceDiagnostic = function () {
  if (typeof navigateToSection === "function") {
    navigateToSection("assistant");
  }
  if (typeof switchStudioTab === "function") {
    switchStudioTab("tab-assistant-chat");
  }
  setTimeout(() => {
    const input = document.getElementById("assistant-input");
    const micBtn = document.getElementById("assistant-mic-btn");
    if (input) input.focus();
    if (micBtn && window.voiceManager && !window.voiceManager.isRecording) {
      micBtn.click();
    }
  }, 200);
};

// ==========================================================================
// 11. Preserved Specialized Analyzers: DTC, Electrical, Thermal, NVH, etc.
// ==========================================================================

function showLoadingInResultBox(targetContainerId, title = "Analyzing Diagnostic Telemetry...") {
  const container = document.getElementById(targetContainerId);
  if (!container) return;
  container.classList.add("visible");
  container.style.display = "block";
  container.innerHTML = `
    <div style="padding: 2.25rem 1.5rem; text-align: center; color: var(--accent-cyan);">
      <div class="status-dot" style="margin: 0 auto 0.85rem; width: 14px; height: 14px; background: var(--accent-cyan); box-shadow: 0 0 14px var(--accent-cyan);"></div>
      <div style="font-weight: 700; font-size: 1.05rem; color: var(--accent-sand); letter-spacing: 0.3px;">${title}</div>
      <div style="font-size: 0.82rem; color: var(--text-dim); margin-top: 0.45rem;">
        Querying ONNX 384d semantic vectors across 9 OEM service manuals & calculating physical probability models...
      </div>
    </div>
  `;
  container.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function renderErrorResult(errMessage, targetContainerId) {
  const container = document.getElementById(targetContainerId);
  if (!container) return;
  container.classList.add("visible");
  container.style.display = "block";
  container.innerHTML = `
    <div style="padding: 1.5rem; background: rgba(239, 68, 68, 0.12); border: 1px solid var(--accent-crimson); border-radius: var(--radius-md); color: #fca5a5;">
      <h3 style="font-size: 1rem; font-weight: 700; margin-bottom: 0.5rem; color: var(--accent-crimson);">⚠️ Diagnostic Computation Error</h3>
      <p style="font-size: 0.85rem; line-height: 1.5;">${errMessage}</p>
      <p style="font-size: 0.75rem; color: var(--text-dim); margin-top: 0.6rem;">Please check your input values and verify that the backend API is reachable.</p>
    </div>
  `;
  container.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function renderDiagnosticResult(result, targetContainerId) {
  state.lastResult = result;
  const container = document.getElementById(targetContainerId);
  if (!container) return;

  if (!result || typeof result !== "object" || !result.subsystem || !result.primary_verdict) {
    const detailMsg = result && result.detail ? result.detail : "Invalid or incomplete diagnostic verdict returned by backend.";
    renderErrorResult(detailMsg, targetContainerId);
    return;
  }

  const isSafe = !!result.is_safe_to_drive;
  const advisoryClass = isSafe ? "advisory-safe" : "advisory-danger";
  const advisoryIcon = isSafe ? "✅" : "⚠️";

  let causesHtml = "";
  if (result.probable_causes && result.probable_causes.length > 0) {
    causesHtml = `
      <h3 style="font-size: 0.95rem; font-weight: 700; margin-bottom: 0.75rem;">Probable Root Causes & Likelihood</h3>
      <div class="cause-list">
        ${result.probable_causes
          .map(
            (c) => `
          <div class="cause-item">
            <div class="cause-top">
              <span>${c.title}</span>
              <span class="cause-prob">${c.probability}%</span>
            </div>
            <div class="progress-track">
              <div class="progress-fill" style="width: ${c.probability}%"></div>
            </div>
            <p class="cause-expl">${c.explanation}</p>
          </div>
        `
          )
          .join("")}
      </div>
    `;
  }

  let stepsHtml = "";
  if (result.action_plan && result.action_plan.length > 0) {
    stepsHtml = `
      <h3 style="font-size: 0.95rem; font-weight: 700; margin-bottom: 0.75rem;">Recommended Diagnostic & Repair Steps</h3>
      <div class="steps-container">
        ${result.action_plan
          .map(
            (s) => `
          <div class="step-row">
            <div class="step-num">${s.step_number}</div>
            <div class="step-content">
              <h4>${s.title}</h4>
              <p>${s.description}</p>
              ${s.tools_needed && s.tools_needed.length > 0 ? `<div class="step-tools">🔧 <strong>Tools:</strong> ${s.tools_needed.join(", ")}</div>` : ""}
            </div>
          </div>
        `
          )
          .join("")}
      </div>
    `;
  }

  let costHtml = "";
  if (result.cost_estimate) {
    const ce = result.cost_estimate;
    const partsDisplay = ce.diy_parts_cost_range_inr || ce.diy_parts_cost_range_usd || "₹0";
    const totalDisplay = ce.professional_total_cost_range_inr || ce.professional_total_cost_range_usd || "₹0";
    costHtml = `
      <h3 style="font-size: 0.95rem; font-weight: 700; margin-bottom: 0.75rem;">Estimated Repair Cost & Difficulty</h3>
      <div class="cost-grid">
        <div class="cost-box">
          <span class="cost-label">DIY Parts Range (₹)</span>
          <span class="cost-val" style="color: var(--accent-cyan);">${partsDisplay}</span>
        </div>
        <div class="cost-box">
          <span class="cost-label">Pro Shop Total (₹)</span>
          <span class="cost-val" style="color: var(--accent-emerald);">${totalDisplay}</span>
        </div>
        <div class="cost-box">
          <span class="cost-label">Labor Estimate</span>
          <span class="cost-val">${ce.professional_labor_hours} hrs</span>
        </div>
        <div class="cost-box">
          <span class="cost-label">Skill Rating</span>
          <span class="cost-val">${ce.difficulty}</span>
        </div>
      </div>
    `;
  }

  let ragHtml = "";
  if (result.rag_reference_chunks && result.rag_reference_chunks.length > 0) {
    ragHtml = `
      <h3 style="font-size: 0.95rem; font-weight: 700; margin-bottom: 0.75rem;">Verified Service Manual References (RAG)</h3>
      <div class="rag-chunks-list">
        ${result.rag_reference_chunks
          .map(
            (chunk) => `
          <div class="rag-chunk-card">
            <div class="rag-chunk-header">
              <span>📖 ${chunk.document_title || "Service Manual"} — ${chunk.section || "Technical Procedure"}</span>
              <span style="font-size: 0.75rem;">Match: ${Math.round((chunk.similarity || 0) * 100)}%</span>
            </div>
            <div class="rag-chunk-text">${chunk.content}</div>
          </div>
        `
          )
          .join("")}
      </div>
    `;
  }

  container.innerHTML = `
    <div class="verdict-header">
      <div>
        <span style="font-size: 0.72rem; text-transform: uppercase; color: var(--accent-cyan); letter-spacing: 0.5px; font-weight: 700;">
          ${result.subsystem}
        </span>
        <h2 class="verdict-title">${result.primary_verdict}</h2>
      </div>
      <div style="display: flex; gap: 0.5rem; align-items: center;">
        <span class="badge-risk badge-${result.urgency}">Urgency: ${result.urgency}</span>
        <button class="btn-icon" onclick="openWorkOrderModal()" style="font-size: 0.75rem;">
          🖨️ Export Work Order
        </button>
      </div>
    </div>

    <div class="advisory-box ${advisoryClass}">
      <span style="font-size: 1.25rem;">${advisoryIcon}</span>
      <div>
        <strong>${isSafe ? "Safe to Drive with Caution" : "DO NOT DRIVE HAZARD"}</strong>
        <p style="margin-top: 0.2rem;">${result.driving_advisory}</p>
      </div>
    </div>

    ${causesHtml}
    ${stepsHtml}
    ${costHtml}
    ${ragHtml}

    <p style="margin-top: 1.25rem; font-size: 0.7rem; color: var(--text-dim); text-align: center;">
      ⚠️ ${result.safety_disclaimer}
    </p>
  `;

  container.classList.add("visible");
  container.style.display = "block";
  container.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

// 2. OBD-II DTC Scanner
function initDTCScanner() {
  const form = document.getElementById("dtc-form");
  const codeInput = document.getElementById("dtc-code-input");
  const quickCodes = document.querySelectorAll(".dtc-quick-code");

  quickCodes.forEach((btn) => {
    btn.addEventListener("click", () => {
      if (codeInput) {
        codeInput.value = btn.dataset.code;
        if (form.requestSubmit) form.requestSubmit();
        else form.dispatchEvent(new Event("submit"));
      }
    });
  });

  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const code = codeInput.value.trim();
    if (!code) return;

    showLoadingInResultBox("dtc-result-box", `Analyzing Diagnostic Trouble Code ${code.toUpperCase()}...`);

    const payload = {
      code: code,
      vehicle_make: state.activeVehicle.make,
      vehicle_model: state.activeVehicle.model,
      include_rag_chunks: true,
      freeze_frame: {
        engine_rpm: parseInt(document.getElementById("ff-rpm")?.value || "0", 10) || null,
        short_term_fuel_trim_pct: parseFloat(document.getElementById("ff-stft")?.value || "0") || null,
        long_term_fuel_trim_pct: parseFloat(document.getElementById("ff-ltft")?.value || "0") || null,
        engine_coolant_temp_f: parseFloat(document.getElementById("ff-ect")?.value || "0") || null,
        battery_voltage: parseFloat(document.getElementById("ff-volt")?.value || "0") || null,
      },
    };

    try {
      const resp = await fetch("/api/analyzers/dtc", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!resp.ok) {
        const errData = await resp.json().catch(() => ({}));
        throw new Error(errData.detail || `Server returned HTTP ${resp.status}`);
      }
      const data = await resp.json();
      renderDiagnosticResult(data, "dtc-result-box");
    } catch (err) {
      renderErrorResult("DTC Analysis error: " + err.message, "dtc-result-box");
    }
  });
}

// 3. Electrical Multimeter Analyzer
function initElectricalAnalyzer() {
  const form = document.getElementById("electrical-form");
  const restingSlider = document.getElementById("resting-voltage-slider");
  const restingVal = document.getElementById("resting-voltage-val");

  if (restingSlider && restingVal) {
    restingSlider.addEventListener("input", () => {
      restingVal.innerText = `${restingSlider.value} V`;
    });
  }

  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    showLoadingInResultBox("electrical-result-box", "Computing Electrical & Multimeter Health Verdict...");

    const payload = {
      resting_voltage: parseFloat(document.getElementById("resting-voltage-slider")?.value || "12.6"),
      cranking_voltage: parseFloat(document.getElementById("cranking-voltage-input")?.value || "10.2"),
      alternator_running_voltage: parseFloat(document.getElementById("alternator-voltage-input")?.value || "14.2"),
      parasitic_draw_ma: parseFloat(document.getElementById("parasitic-draw-input")?.value || "35.0"),
      battery_age_years: parseFloat(document.getElementById("battery-age-input")?.value || "2.0"),
      include_rag_chunks: true,
    };

    try {
      const resp = await fetch("/api/analyzers/electrical", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!resp.ok) {
        const errData = await resp.json().catch(() => ({}));
        throw new Error(errData.detail || `Server returned HTTP ${resp.status}`);
      }
      const data = await resp.json();
      renderDiagnosticResult(data, "electrical-result-box");
    } catch (err) {
      renderErrorResult("Electrical Analysis error: " + err.message, "electrical-result-box");
    }
  });
}

// 4. Thermal / Overheating Analyzer
function initThermalAnalyzer() {
  const form = document.getElementById("thermal-form");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    showLoadingInResultBox("thermal-result-box", "Simulating Cooling System Thermodynamics & Head Gasket Integrity...");

    const payload = {
      driving_condition: document.getElementById("thermal-condition")?.value || "idle_traffic",
      coolant_level: document.getElementById("thermal-coolant-level")?.value || "normal",
      electric_fan_running: document.getElementById("thermal-fan-status")?.value || "unknown",
      cabin_heater_output: document.getElementById("thermal-heater-output")?.value || "hot",
      hose_temperature_differential: document.getElementById("thermal-hose-temp")?.value || "unknown",
      white_exhaust_smoke_or_milky_oil: document.getElementById("thermal-smoke-oil")?.checked || false,
      include_rag_chunks: true,
    };

    try {
      const resp = await fetch("/api/analyzers/thermal", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!resp.ok) {
        const errData = await resp.json().catch(() => ({}));
        throw new Error(errData.detail || `Server returned HTTP ${resp.status}`);
      }
      const data = await resp.json();
      renderDiagnosticResult(data, "thermal-result-box");
    } catch (err) {
      renderErrorResult("Thermal Analysis error: " + err.message, "thermal-result-box");
    }
  });
}

// 5. Brake System Analyzer
function initBrakeAnalyzer() {
  const form = document.getElementById("brake-form");
  const padSlider = document.getElementById("brake-pad-slider");
  const padVal = document.getElementById("brake-pad-val");

  if (padSlider && padVal) {
    padSlider.addEventListener("input", () => {
      const mm = parseFloat(padSlider.value);
      padVal.innerText = `${mm} mm (${mm <= 2 ? "CRITICAL" : mm <= 4 ? "CAUTION" : "GOOD"})`;
      padVal.style.color = mm <= 2 ? "var(--accent-crimson)" : mm <= 4 ? "var(--accent-amber)" : "var(--accent-emerald)";
    });
  }

  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    showLoadingInResultBox("brake-result-box", "Evaluating Hydraulic Brake Safety & Wear Thresholds...");

    const payload = {
      pad_thickness_mm: parseFloat(document.getElementById("brake-pad-slider")?.value || "3.0"),
      pedal_feel: document.getElementById("brake-pedal-feel")?.value || "normal_firm",
      rotor_condition: document.getElementById("brake-rotor-cond")?.value || "smooth",
      pulls_when_braking: document.getElementById("brake-pull")?.value || "none",
      include_rag_chunks: true,
    };

    try {
      const resp = await fetch("/api/analyzers/brake", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!resp.ok) {
        const errData = await resp.json().catch(() => ({}));
        throw new Error(errData.detail || `Server returned HTTP ${resp.status}`);
      }
      const data = await resp.json();
      renderDiagnosticResult(data, "brake-result-box");
    } catch (err) {
      renderErrorResult("Brake Analysis error: " + err.message, "brake-result-box");
    }
  });
}

// 7. Transmission & Drivetrain Analyzer
function initDrivetrainAnalyzer() {
  const form = document.getElementById("drivetrain-form");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    showLoadingInResultBox("drivetrain-result-box", "Analyzing Transmission Hydraulics & Torque Slip Ratios...");

    const payload = {
      transmission_type: document.getElementById("trans-type")?.value || "automatic_torque_converter",
      symptom: document.getElementById("trans-symptom")?.value || "slipping_rpm_flares",
      fluid_color: document.getElementById("trans-fluid-color")?.value || "cherry_red_clean",
      fluid_level: document.getElementById("trans-fluid-level")?.value || "normal",
      include_rag_chunks: true,
    };

    try {
      const resp = await fetch("/api/analyzers/drivetrain", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!resp.ok) {
        const errData = await resp.json().catch(() => ({}));
        throw new Error(errData.detail || `Server returned HTTP ${resp.status}`);
      }
      const data = await resp.json();
      renderDiagnosticResult(data, "drivetrain-result-box");
    } catch (err) {
      renderErrorResult("Drivetrain Analysis error: " + err.message, "drivetrain-result-box");
    }
  });
}

// 8. Fuel Trim & Emissions Analyzer
function initEmissionsAnalyzer() {
  const form = document.getElementById("emissions-form");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    showLoadingInResultBox("emissions-result-box", "Calculating Stoichiometric Mixture Imbalances & Vacuum Leaks...");

    const payload = {
      stft_idle_pct: parseFloat(document.getElementById("em-stft-idle")?.value || "0.0"),
      ltft_idle_pct: parseFloat(document.getElementById("em-ltft-idle")?.value || "0.0"),
      stft_2500rpm_pct: parseFloat(document.getElementById("em-stft-2500")?.value || "0.0"),
      ltft_2500rpm_pct: parseFloat(document.getElementById("em-ltft-2500")?.value || "0.0"),
      exhaust_smoke_color: document.getElementById("em-exhaust-smoke")?.value || "none",
      raw_fuel_odor: false,
      include_rag_chunks: true,
    };

    try {
      const resp = await fetch("/api/analyzers/emissions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!resp.ok) {
        const errData = await resp.json().catch(() => ({}));
        throw new Error(errData.detail || `Server returned HTTP ${resp.status}`);
      }
      const data = await resp.json();
      renderDiagnosticResult(data, "emissions-result-box");
    } catch (err) {
      renderErrorResult("Emissions Analysis error: " + err.message, "emissions-result-box");
    }
  });
}

// 9. Interactive Problem Wizard
function initWizard() {
  const domainBtns = document.querySelectorAll(".wizard-domain-btn");
  const stageDomains = document.getElementById("wizard-stage-domains");
  const stageQuestions = document.getElementById("wizard-stage-questions");

  domainBtns.forEach((btn) => {
    btn.addEventListener("click", async () => {
      const domain = btn.dataset.domain;
      state.wizard.domain = domain;
      state.wizard.answers = {};
      state.wizard.currentStep = 0;

      try {
        const resp = await fetch("/api/analyzers/wizard/start", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ domain: domain }),
        });
        const data = await resp.json();
        state.wizard.questions = data.questions || [];

        if (stageDomains) stageDomains.style.display = "none";
        if (stageQuestions) stageQuestions.style.display = "block";
        renderWizardQuestion();
      } catch (err) {
        alert("Failed to start wizard: " + err.message);
      }
    });
  });
}

function renderWizardQuestion() {
  const container = document.getElementById("wizard-question-content");
  if (!container) return;

  const q = state.wizard.questions[state.wizard.currentStep];
  if (!q) {
    finalizeWizard();
    return;
  }

  container.innerHTML = `
    <div style="margin-bottom: 1.25rem;">
      <span style="font-size: 0.75rem; text-transform: uppercase; color: var(--accent-cyan); font-weight: 700;">
        Step ${state.wizard.currentStep + 1} of ${state.wizard.questions.length}
      </span>
      <h3 style="font-size: 1.15rem; font-weight: 700; margin-top: 0.25rem;">${q.prompt}</h3>
    </div>

    <div class="wizard-options-grid">
      ${q.options
        .map(
          (opt) => `
        <button class="wizard-opt-btn" onclick="selectWizardOption('${q.id}', '${opt.id}')">
          <span class="opt-title">${opt.label}</span>
          ${opt.hint ? `<span class="opt-hint">${opt.hint}</span>` : ""}
        </button>
      `
        )
        .join("")}
    </div>
  `;
}

window.selectWizardOption = function (questionId, optionId) {
  state.wizard.answers[questionId] = optionId;
  state.wizard.currentStep += 1;

  if (state.wizard.currentStep < state.wizard.questions.length) {
    renderWizardQuestion();
  } else {
    finalizeWizard();
  }
};

async function finalizeWizard() {
  const container = document.getElementById("wizard-question-content");
  if (container) {
    container.innerHTML = `
      <div style="padding: 2rem; text-align: center; color: var(--accent-cyan);">
        <div class="status-dot" style="margin: 0 auto 0.75rem; width: 12px; height: 12px;"></div>
        Synthesizing symptom answers and cross-referencing automotive service manuals...
      </div>
    `;
  }

  showLoadingInResultBox("wizard-result-box", "Synthesizing Interactive Troubleshooting Decisions...");

  try {
    const resp = await fetch("/api/analyzers/wizard/step", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        domain: state.wizard.domain,
        answers: state.wizard.answers,
        include_rag_chunks: true,
      }),
    });
    if (!resp.ok) {
      const errData = await resp.json().catch(() => ({}));
      throw new Error(errData.detail || `Server returned HTTP ${resp.status}`);
    }
    const data = await resp.json();
    renderDiagnosticResult(data, "wizard-result-box");

    if (container) {
      container.innerHTML = `
        <div style="text-align: center; padding: 1.5rem;">
          <h3 style="font-size: 1.1rem; color: var(--accent-emerald);">Diagnostic Work Order Generated Below</h3>
          <button class="btn-primary" onclick="resetWizard()" style="margin-top: 1rem;">
            🔄 Run Another Diagnostic Case
          </button>
        </div>
      `;
    }
  } catch (err) {
    renderErrorResult("Wizard evaluation failed: " + err.message, "wizard-result-box");
  }
}

window.resetWizard = function () {
  const stageDomains = document.getElementById("wizard-stage-domains");
  const stageQuestions = document.getElementById("wizard-stage-questions");
  const resultBox = document.getElementById("wizard-result-box");

  if (stageDomains) stageDomains.style.display = "block";
  if (stageQuestions) stageQuestions.style.display = "none";
  if (resultBox) {
    resultBox.classList.remove("visible");
    resultBox.innerHTML = "";
  }
};

// 10. Printable Work Order Modal
function initWorkOrderModal() {
  const modal = document.getElementById("work-order-modal");
  const closeBtn = document.getElementById("modal-close-btn");

  if (closeBtn && modal) {
    closeBtn.addEventListener("click", () => modal.classList.remove("open"));
  }
  window.addEventListener("click", (e) => {
    if (e.target === modal) modal.classList.remove("open");
  });
}

window.openWorkOrderModal = function () {
  const modal = document.getElementById("work-order-modal");
  const content = document.getElementById("work-order-content");
  if (!modal || !content) return;

  const res = state.lastResult;
  if (!res) {
    alert("Please run a diagnostic analysis first before generating a work order.");
    return;
  }

  const v = state.activeVehicle;
  const today = new Date().toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" });

  content.innerHTML = `
    <div style="border-bottom: 2px solid var(--border-color); padding-bottom: 1rem; margin-bottom: 1.25rem;">
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
          <h2 style="font-size: 1.5rem; font-weight: 800; letter-spacing: -0.5px;">AUTOASSIST AI REPAIR ORDER</h2>
          <p style="font-size: 0.78rem; color: var(--text-muted);">Informational Diagnostic Sheet & Reference Guide</p>
        </div>
        <div style="text-align: right; font-size: 0.8rem; color: var(--text-muted);">
          <div>Date: <strong>${today}</strong></div>
          <div>RO Number: <strong>#AGY-${Math.floor(100000 + Math.random() * 900000)}</strong></div>
        </div>
      </div>
    </div>

    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.75rem; background: var(--bg-card); padding: 0.85rem; border-radius: 8px; margin-bottom: 1.25rem; font-size: 0.82rem;">
      <div><span style="color: var(--text-dim);">Vehicle Make:</span><br><strong>${v.make}</strong></div>
      <div><span style="color: var(--text-dim);">Model:</span><br><strong>${v.model}</strong></div>
      <div><span style="color: var(--text-dim);">Year:</span><br><strong>${v.year}</strong></div>
      <div><span style="color: var(--text-dim);">Mileage:</span><br><strong>${(v.mileage_km || 45000).toLocaleString()} km</strong></div>
    </div>

    <div style="margin-bottom: 1.25rem;">
      <h3 style="font-size: 0.95rem; font-weight: 700; color: var(--accent-cyan); text-transform: uppercase;">1. Diagnostic Verdict</h3>
      <p style="font-size: 1.15rem; font-weight: 700; margin: 0.35rem 0;">${res.primary_verdict}</p>
      <div style="font-size: 0.85rem; padding: 0.5rem 0.75rem; background: rgba(56, 189, 248, 0.1); border-left: 3px solid var(--accent-cyan); border-radius: 4px;">
        <strong>Safety Advisory:</strong> ${res.driving_advisory}
      </div>
    </div>

    <div style="margin-bottom: 1.25rem;">
      <h3 style="font-size: 0.95rem; font-weight: 700; color: var(--accent-cyan); text-transform: uppercase;">2. Root Causes Identified</h3>
      <ul style="margin-left: 1.25rem; margin-top: 0.5rem; font-size: 0.85rem; line-height: 1.5;">
        ${res.probable_causes ? res.probable_causes.map((c) => `<li><strong>${c.title}</strong> (${c.probability}% likelihood) — ${c.explanation}</li>`).join("") : ""}
      </ul>
    </div>

    <div style="display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 1.5rem; border-top: 1px solid var(--border-color); padding-top: 1rem;">
      <button class="btn-primary" onclick="window.print()">🖨️ Print / Save as PDF</button>
    </div>
  `;

  modal.classList.add("open");
};

// 11. 1-Click Simulations Runner
window.runDemo = function (demoType) {
  navigateToSection("assistant");

  if (demoType === "dtc_p0300") {
    switchStudioTab("tab-dtc");
    setTimeout(() => {
      const dtcInput = document.getElementById("dtc-code-input");
      const rpm = document.getElementById("ff-rpm");
      const stft = document.getElementById("ff-stft");
      const ltft = document.getElementById("ff-ltft");
      const ect = document.getElementById("ff-ect");
      const volt = document.getElementById("ff-volt");
      const dtcForm = document.getElementById("dtc-form");
      if (dtcInput) dtcInput.value = "P0300";
      if (rpm) rpm.value = "750";
      if (stft) stft.value = "3.5";
      if (ltft) ltft.value = "18.5";
      if (ect) ect.value = "195";
      if (volt) volt.value = "13.8";
      if (dtcForm) {
        if (dtcForm.requestSubmit) dtcForm.requestSubmit();
        else dtcForm.dispatchEvent(new Event("submit"));
      }
    }, 150);
  } else if (demoType === "elec_battery") {
    switchStudioTab("tab-electrical");
    setTimeout(() => {
      const voltSlider = document.getElementById("resting-voltage-slider");
      const voltVal = document.getElementById("resting-voltage-val");
      const crankInput = document.getElementById("cranking-voltage-input");
      const altInput = document.getElementById("alternator-voltage-input");
      const elForm = document.getElementById("electrical-form");
      if (voltSlider) voltSlider.value = "10.2";
      if (voltVal) voltVal.innerText = "10.2 V";
      if (crankInput) crankInput.value = "7.6";
      if (altInput) altInput.value = "13.2";
      if (elForm) {
        if (elForm.requestSubmit) elForm.requestSubmit();
        else elForm.dispatchEvent(new Event("submit"));
      }
    }, 150);
  } else if (demoType === "thermal_overheat") {
    switchStudioTab("tab-thermal");
    setTimeout(() => {
      const cond = document.getElementById("thermal-condition");
      const level = document.getElementById("thermal-coolant-level");
      const fan = document.getElementById("thermal-fan-status");
      const hose = document.getElementById("thermal-hose-temp");
      const thForm = document.getElementById("thermal-form");
      if (cond) cond.value = "idle_traffic";
      if (level) level.value = "normal";
      if (fan) fan.value = "no_not_spinning";
      if (hose) hose.value = "upper_scalding_lower_cold";
      if (thForm) {
        if (thForm.requestSubmit) thForm.requestSubmit();
        else thForm.dispatchEvent(new Event("submit"));
      }
    }, 150);
  }
};

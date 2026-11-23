/**
 * AutoAssist AI - Client Application Logic
 * Powers RAG Semantic Search, Dedicated Problem Analyzers, and Guided Diagnostic Wizard.
 */

// Global State
const state = {
  currentVehicle: {
    make: "Honda",
    model: "Civic",
    year: 2022,
    mileage: 45000,
  },
  lastResult: null,
  wizard: {
    domain: null,
    questions: [],
    currentStep: 0,
    answers: {},
  },
};

// DOM Content Loaded
document.addEventListener("DOMContentLoaded", () => {
  try {
    initCinematicIntro();
  } catch (err) {
    console.warn("Cinematic intro canvas initialization deferred/skipped:", err);
  }
  initTabs();
  initTheme();
  initVehicleBar();
  initRAGSearch();
  initDTCScanner();
  initElectricalAnalyzer();
  initThermalAnalyzer();
  initAcousticAnalyzer();
  initBrakeAnalyzer();
  initDrivetrainAnalyzer();
  initEmissionsAnalyzer();
  initWizard();
  loadPriceGuide();
  initWorkOrderModal();
});

// Tab Navigation
function initTabs() {
  const tabBtns = document.querySelectorAll(".tab-btn");
  tabBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      const targetId = btn.dataset.tab;
      if (typeof window.switchStudioTab === "function") {
        window.switchStudioTab(targetId);
      } else {
        const tabPanels = document.querySelectorAll(".tab-panel");
        tabBtns.forEach((b) => b.classList.remove("active"));
        tabPanels.forEach((p) => {
          p.classList.remove("active");
          p.style.display = "none";
        });
        btn.classList.add("active");
        const targetPanel = document.getElementById(targetId);
        if (targetPanel) {
          targetPanel.classList.add("active");
          targetPanel.style.display = "block";
        }
      }
    });
  });
}

// Dark / Light Theme Toggle
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

// Vehicle Selection State
function initVehicleBar() {
  const makeSel = document.getElementById("vehicle-make");
  const modelSel = document.getElementById("vehicle-model");
  const yearSel = document.getElementById("vehicle-year");
  const mileageInput = document.getElementById("vehicle-mileage");

  function updateVehicle() {
    state.currentVehicle = {
      make: makeSel ? makeSel.value : "Generic",
      model: modelSel ? modelSel.value : "Generic",
      year: yearSel ? parseInt(yearSel.value, 10) : 2022,
      mileage: mileageInput ? parseInt(mileageInput.value, 10) : 45000,
    };
  }

  if (makeSel) makeSel.addEventListener("change", updateVehicle);
  if (modelSel) modelSel.addEventListener("change", updateVehicle);
  if (yearSel) yearSel.addEventListener("change", updateVehicle);
  if (mileageInput) mileageInput.addEventListener("change", updateVehicle);
}

// Immediate Loading State Feedback for Result Box
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

// Error Feedback for Result Box
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

// Render Universal Diagnostic Result Box
function renderDiagnosticResult(result, targetContainerId) {
  state.lastResult = result;
  const container = document.getElementById(targetContainerId);
  if (!container) return;

  if (!result || typeof result !== "object" || !result.subsystem || !result.primary_verdict) {
    const detailMsg = (result && result.detail) ? result.detail : "Invalid or incomplete diagnostic verdict returned by backend.";
    renderErrorResult(detailMsg, targetContainerId);
    return;
  }

  const isSafe = !!result.is_safe_to_drive;
  const advisoryClass = isSafe ? "advisory-safe" : "advisory-danger";
  const advisoryIcon = isSafe ? "✅" : "⚠️";

  // Build Probabilities
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

  // Build Action Steps
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
              ${
                s.tools_needed && s.tools_needed.length > 0
                  ? `<div class="step-tools">🔧 <strong>Tools:</strong> ${s.tools_needed.join(", ")}</div>`
                  : ""
              }
            </div>
          </div>
        `
          )
          .join("")}
      </div>
    `;
  }

  // Build Cost Estimate
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

  // Build RAG Manual References
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

// 1. RAG Semantic Knowledge Search
function initRAGSearch() {
  const form = document.getElementById("rag-search-form");
  const input = document.getElementById("rag-query-input");
  const resultsContainer = document.getElementById("rag-results");
  const quickChips = document.querySelectorAll(".rag-quick-chip");

  quickChips.forEach((chip) => {
    chip.addEventListener("click", () => {
      if (input) {
        input.value = chip.dataset.query;
        form.dispatchEvent(new Event("submit"));
      }
    });
  });

  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const query = input.value.trim();
    if (!query) return;

    resultsContainer.innerHTML = `
      <div style="padding: 2rem; text-align: center; color: var(--accent-cyan);">
        <div class="status-dot" style="margin: 0 auto 0.75rem; width: 12px; height: 12px;"></div>
        Searching 129 technical manual chunks with 384d semantic embeddings...
      </div>
    `;

    try {
      const resp = await fetch("/api/rag/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: query,
          top_k: 5,
          similarity_threshold: 0.20,
          manufacturer: state.currentVehicle.make !== "Generic" ? state.currentVehicle.make : null,
        }),
      });

      if (!resp.ok) {
        throw new Error(`Server returned HTTP ${resp.status}`);
      }

      const data = await resp.json();
      renderRAGSearchResults(data, resultsContainer);
    } catch (err) {
      resultsContainer.innerHTML = `
        <div style="padding: 1.5rem; background: rgba(239, 68, 68, 0.1); border: 1px solid var(--accent-crimson); border-radius: 8px; color: #fca5a5;">
          <strong>Retrieval Error:</strong> ${err.message}. Please verify the backend is running.
        </div>
      `;
    }
  });
}

function renderRAGSearchResults(data, container) {
  if (!data.results || data.results.length === 0) {
    container.innerHTML = `
      <div style="padding: 2rem; text-align: center; color: var(--text-muted);">
        No technical manual sections met the similarity threshold for this query. Try rephrasing your mechanical symptom.
      </div>
    `;
    return;
  }

  container.innerHTML = `
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
      <span style="font-size: 0.85rem; color: var(--text-muted);">
        Found <strong>${data.total_results}</strong> matches in <strong>${data.latency_ms.toFixed(1)}ms</strong>
      </span>
      <span style="font-size: 0.75rem; color: var(--accent-cyan); font-family: monospace;">all-MiniLM-L6-v2 ONNX</span>
    </div>

    <div class="rag-chunks-list">
      ${data.results
        .map(
          (item, idx) => `
        <div class="rag-chunk-card" style="border-left-width: 4px;">
          <div class="rag-chunk-header">
            <div>
              <span style="background: rgba(223, 202, 167, 0.15); color: var(--accent-cyan); padding: 0.15rem 0.5rem; border-radius: 4px; font-size: 0.75rem; margin-right: 0.5rem;">#${idx + 1}</span>
              <strong>${item.document_title}</strong>
              <span style="color: var(--text-dim); font-size: 0.75rem;"> • ${item.section || "Technical Guide"} (Page ${item.page_number || 1})</span>
            </div>
            <div style="font-family: monospace; font-size: 0.8rem; color: var(--accent-cyan);">
              Cosine Sim: ${item.similarity.toFixed(4)}
            </div>
          </div>
          <div class="rag-chunk-text" style="font-size: 0.85rem; margin-top: 0.5rem;">${item.content}</div>
        </div>
      `
        )
        .join("")}
    </div>
  `;
}

// 2. OBD-II / DTC Scanner
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
      vehicle_make: state.currentVehicle.make,
      vehicle_model: state.currentVehicle.model,
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

// 5. NVH Acoustic Sound Analyzer
function initAcousticAnalyzer() {
  const form = document.getElementById("acoustic-form");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    showLoadingInResultBox("acoustic-result-box", "Matching NVH Harmonic Spectrum & Component Resonances...");

    const payload = {
      sound_type: document.getElementById("sound-type")?.value || "squeal_chirp",
      location: document.getElementById("sound-location")?.value || "front_wheel_brakes",
      condition: document.getElementById("sound-condition")?.value || "when_braking",
      speed_dependent: document.getElementById("sound-speed-dep")?.checked || false,
      rpm_dependent: document.getElementById("sound-rpm-dep")?.checked || false,
      include_rag_chunks: true,
    };

    try {
      const resp = await fetch("/api/analyzers/acoustic", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!resp.ok) {
        const errData = await resp.json().catch(() => ({}));
        throw new Error(errData.detail || `Server returned HTTP ${resp.status}`);
      }
      const data = await resp.json();
      renderDiagnosticResult(data, "acoustic-result-box");
    } catch (err) {
      renderErrorResult("Acoustic Analysis error: " + err.message, "acoustic-result-box");
    }
  });
}

// 6. Brake System Analyzer
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
      abs_warning_light: document.getElementById("brake-abs-light")?.checked || false,
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
      raw_fuel_odor: document.getElementById("em-fuel-smell")?.checked || false,
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

// 9. Interactive Guided Diagnostic Wizard
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

// 10. Load Price Guide Table
async function loadPriceGuide() {
  const tbody = document.getElementById("price-guide-tbody");
  if (!tbody) return;

  try {
    const resp = await fetch("/api/analyzers/repairs/price-guide");
    const data = await resp.json();

    const rows = Object.entries(data).map(([key, item]) => {
      const cleanName = key
        .replace(/_/g, " ")
        .replace(/\b\w/g, (l) => l.toUpperCase());
      return `
        <tr>
          <td style="padding: 0.75rem 1rem; font-weight: 600; color: var(--text-main);">${cleanName}</td>
          <td style="padding: 0.75rem 1rem; color: var(--accent-cyan);">${item.parts}</td>
          <td style="padding: 0.75rem 1rem; color: var(--text-muted);">${item.labor_hours} hrs</td>
          <td style="padding: 0.75rem 1rem; font-weight: 700; color: var(--accent-emerald);">${item.pro_total}</td>
          <td style="padding: 0.75rem 1rem;"><span class="badge-risk badge-MEDIUM" style="font-size: 0.7rem;">${item.difficulty}</span></td>
        </tr>
      `;
    });

    tbody.innerHTML = rows.join("");
  } catch (e) {
    console.error("Could not load price guide:", e);
  }
}

// Printable Work Order Modal
function initWorkOrderModal() {
  const modal = document.getElementById("work-order-modal");
  const closeBtn = document.getElementById("modal-close-btn");

  if (closeBtn && modal) {
    closeBtn.addEventListener("click", () => {
      modal.classList.remove("open");
    });
  }

  window.addEventListener("click", (e) => {
    if (e.target === modal) {
      modal.classList.remove("open");
    }
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

  const v = state.currentVehicle;
  const today = new Date().toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  content.innerHTML = `
    <div style="border-bottom: 2px solid var(--border-color); padding-bottom: 1rem; margin-bottom: 1.25rem;">
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
          <h2 style="font-size: 1.5rem; font-weight: 800; letter-spacing: -0.5px;">AUTOASSIST AI REPAIR ORDER</h2>
          <p style="font-size: 0.78rem; color: var(--text-muted);">Certified Diagnostic Sheet & Mechanical Assessment</p>
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
      <div><span style="color: var(--text-dim);">Mileage:</span><br><strong>${v.mileage.toLocaleString()} mi</strong></div>
    </div>

    <div style="margin-bottom: 1.25rem;">
      <h3 style="font-size: 0.95rem; font-weight: 700; color: var(--accent-cyan); text-transform: uppercase;">1. Diagnostic Verdict</h3>
      <p style="font-size: 1.15rem; font-weight: 700; margin: 0.35rem 0;">${res.primary_verdict}</p>
      <div style="font-size: 0.85rem; padding: 0.5rem 0.75rem; background: rgba(223, 202, 167, 0.1); border-left: 3px solid var(--accent-cyan); border-radius: 4px;">
        <strong>Safety Advisory:</strong> ${res.driving_advisory}
      </div>
    </div>

    <div style="margin-bottom: 1.25rem;">
      <h3 style="font-size: 0.95rem; font-weight: 700; color: var(--accent-cyan); text-transform: uppercase;">2. Root Causes Identified</h3>
      <ul style="margin-left: 1.25rem; margin-top: 0.5rem; font-size: 0.85rem; line-height: 1.5;">
        ${res.probable_causes
          .map(
            (c) => `<li><strong>${c.title}</strong> (${c.probability}% likelihood) — ${c.explanation}</li>`
          )
          .join("")}
      </ul>
    </div>

    <div style="margin-bottom: 1.25rem;">
      <h3 style="font-size: 0.95rem; font-weight: 700; color: var(--accent-cyan); text-transform: uppercase;">3. Prescribed Action Steps</h3>
      <ol style="margin-left: 1.25rem; margin-top: 0.5rem; font-size: 0.85rem; line-height: 1.5;">
        ${res.action_plan
          .map(
            (s) => `<li><strong>${s.title}:</strong> ${s.description} ${s.tools_needed && s.tools_needed.length > 0 ? `<em>(Tools: ${s.tools_needed.join(", ")})</em>` : ""}</li>`
          )
          .join("")}
      </ol>
    </div>

    ${
      res.cost_estimate
        ? `
      <div style="margin-bottom: 1.5rem;">
        <h3 style="font-size: 0.95rem; font-weight: 700; color: var(--accent-cyan); text-transform: uppercase;">4. Estimated Cost & Labor</h3>
        <div style="display: flex; gap: 1.5rem; font-size: 0.85rem; margin-top: 0.4rem;">
          <div>Parts Cost (INR): <strong>${res.cost_estimate.diy_parts_cost_range_inr || res.cost_estimate.diy_parts_cost_range_usd}</strong></div>
          <div>Labor Hours: <strong>${res.cost_estimate.professional_labor_hours} hrs</strong></div>
          <div>Pro Shop Total (INR): <strong>${res.cost_estimate.professional_total_cost_range_inr || res.cost_estimate.professional_total_cost_range_usd}</strong></div>
        </div>
      </div>
    `
        : ""
    }

    <div style="display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 1.5rem; border-top: 1px solid var(--border-color); padding-top: 1rem;">
      <button class="btn-primary" onclick="window.print()">🖨️ Print / Save as PDF</button>
    </div>
  `;

  modal.classList.add("open");
};

// ==========================================================================
// View Routing & Cinematic Intro Controller (Forest Green & Sand Beige)
// ==========================================================================

// Global Studio Tab Switcher: directly activates both the tab button and the panel
window.switchStudioTab = function(tabId) {
  const tabBtns = document.querySelectorAll(".tab-btn");
  const tabPanels = document.querySelectorAll(".tab-panel");

  tabBtns.forEach((b) => {
    if (b.getAttribute("data-tab") === tabId) {
      b.classList.add("active");
    } else {
      b.classList.remove("active");
    }
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

// Global View Switcher: easily switch between 'intro' and 'studio'
window.navigateToView = function(viewName, targetTabId = null) {
  const viewIntro = document.getElementById("view-intro");
  const viewStudio = document.getElementById("view-studio");
  const navBtnIntro = document.getElementById("nav-btn-intro");
  const navBtnStudio = document.getElementById("nav-btn-studio");

  if (viewName === "studio") {
    if (viewIntro) {
      viewIntro.classList.remove("active");
      viewIntro.style.display = "none";
    }
    if (viewStudio) {
      viewStudio.classList.add("active");
      viewStudio.style.display = "block";
    }
    if (navBtnIntro) navBtnIntro.classList.remove("active");
    if (navBtnStudio) navBtnStudio.classList.add("active");

    if (targetTabId) {
      window.switchStudioTab(targetTabId);
    } else {
      const activeTab = document.querySelector(".tab-btn.active");
      if (activeTab && activeTab.getAttribute("data-tab")) {
        window.switchStudioTab(activeTab.getAttribute("data-tab"));
      } else {
        window.switchStudioTab("tab-rag");
      }
    }
    window.scrollTo({ top: 0, behavior: "smooth" });
  } else {
    // Navigate to intro
    if (viewStudio) {
      viewStudio.classList.remove("active");
      viewStudio.style.display = "none";
    }
    if (viewIntro) {
      viewIntro.classList.add("active");
      viewIntro.style.display = "block";
    }
    if (navBtnStudio) navBtnStudio.classList.remove("active");
    if (navBtnIntro) navBtnIntro.classList.add("active");

    window.scrollTo({ top: 0, behavior: "smooth" });
  }
};

// Global Quick 1-Click Interactive Diagnostic Demo Runner
window.runDemo = function(demoType) {
  if (demoType === "dtc_p0300") {
    window.navigateToView("studio", "tab-dtc");
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
    window.navigateToView("studio", "tab-electrical");
    setTimeout(() => {
      const voltSlider = document.getElementById("resting-voltage-slider");
      const voltVal = document.getElementById("resting-voltage-val");
      const crankInput = document.getElementById("cranking-voltage-input");
      const altInput = document.getElementById("alternator-voltage-input");
      const drawInput = document.getElementById("parasitic-draw-input");
      const ageInput = document.getElementById("battery-age-input");
      const elForm = document.getElementById("electrical-form");
      if (voltSlider) voltSlider.value = "10.2";
      if (voltVal) voltVal.innerText = "10.2 V";
      if (crankInput) crankInput.value = "7.6";
      if (altInput) altInput.value = "13.2";
      if (drawInput) drawInput.value = "120";
      if (ageInput) ageInput.value = "4.5";
      if (elForm) {
        if (elForm.requestSubmit) elForm.requestSubmit();
        else elForm.dispatchEvent(new Event("submit"));
      }
    }, 150);
  } else if (demoType === "thermal_overheat") {
    window.navigateToView("studio", "tab-thermal");
    setTimeout(() => {
      const cond = document.getElementById("thermal-condition");
      const level = document.getElementById("thermal-coolant-level");
      const fan = document.getElementById("thermal-fan-status");
      const heater = document.getElementById("thermal-heater-output");
      const hose = document.getElementById("thermal-hose-temp");
      const smoke = document.getElementById("thermal-smoke-oil");
      const thForm = document.getElementById("thermal-form");
      if (cond) cond.value = "idle_traffic";
      if (level) level.value = "normal";
      if (fan) fan.value = "no_not_spinning";
      if (heater) heater.value = "hot";
      if (hose) hose.value = "upper_scalding_lower_cold";
      if (smoke) smoke.checked = false;
      if (thForm) {
        if (thForm.requestSubmit) thForm.requestSubmit();
        else thForm.dispatchEvent(new Event("submit"));
      }
    }, 150);
  } else if (demoType === "acoustic_whine") {
    window.navigateToView("studio", "tab-acoustic");
    setTimeout(() => {
      const soundType = document.getElementById("sound-type");
      const location = document.getElementById("sound-location");
      const condition = document.getElementById("sound-condition");
      const rpmDep = document.getElementById("sound-rpm-dep");
      const speedDep = document.getElementById("sound-speed-dep");
      const acForm = document.getElementById("acoustic-form");
      if (soundType) soundType.value = "whine_hum";
      if (location) location.value = "engine_front_belt";
      if (condition) condition.value = "accelerating";
      if (rpmDep) rpmDep.checked = true;
      if (speedDep) speedDep.checked = false;
      if (acForm) {
        if (acForm.requestSubmit) acForm.requestSubmit();
        else acForm.dispatchEvent(new Event("submit"));
      }
    }, 150);
  }
};

function initCinematicIntro() {
  const intro = document.getElementById("cinematic-intro");
  const canvas = document.getElementById("cinematic-canvas");

  // Telemetry Radar Canvas Animation
  if (!canvas || !intro) return;
  const ctx = canvas.getContext("2d");
  let width = (canvas.width = intro.offsetWidth || window.innerWidth);
  let height = (canvas.height = intro.offsetHeight || 700);

  let mouse = { x: width / 2, y: height / 2, active: false };

  window.addEventListener("resize", () => {
    const viewIntro = document.getElementById("view-intro");
    if (viewIntro && viewIntro.classList.contains("active")) {
      width = canvas.width = intro.offsetWidth || window.innerWidth;
      height = canvas.height = intro.offsetHeight || 700;
    }
  });

  intro.addEventListener("mousemove", (e) => {
    const rect = canvas.getBoundingClientRect();
    mouse.x = e.clientX - rect.left;
    mouse.y = e.clientY - rect.top;
    mouse.active = true;
  });

  intro.addEventListener("mouseleave", () => {
    mouse.active = false;
  });

  const nodeCount = Math.min(50, Math.max(25, Math.floor((width * height) / 20000)));
  const nodes = [];
  const palette = [
    { color: "rgba(223, 202, 167, 0.75)", radius: 2.2 }, // Sand Beige
    { color: "rgba(82, 183, 136, 0.7)", radius: 2.0 },  // Forest Emerald
    { color: "rgba(245, 236, 224, 0.8)", radius: 1.8 }, // Pale Sand
    { color: "rgba(45, 106, 79, 0.65)", radius: 2.4 },  // Pine Green
  ];

  for (let i = 0; i < nodeCount; i++) {
    const p = palette[Math.floor(Math.random() * palette.length)];
    nodes.push({
      x: Math.random() * width,
      y: Math.random() * height,
      vx: (Math.random() - 0.5) * 0.5,
      vy: (Math.random() - 0.5) * 0.5,
      radius: p.radius,
      color: p.color,
    });
  }

  let scanlineY = 0;

  function render() {
    const viewIntro = document.getElementById("view-intro");
    if (!viewIntro || !viewIntro.classList.contains("active")) {
      requestAnimationFrame(render);
      return;
    }

    ctx.clearRect(0, 0, width, height);

    // Subtle Automotive Radar Scanline Sweep
    scanlineY = (scanlineY + 1.2) % height;
    const scanGradient = ctx.createLinearGradient(0, scanlineY - 35, 0, scanlineY + 35);
    scanGradient.addColorStop(0, "rgba(82, 183, 136, 0)");
    scanGradient.addColorStop(0.5, "rgba(223, 202, 167, 0.08)");
    scanGradient.addColorStop(1, "rgba(82, 183, 136, 0)");
    ctx.fillStyle = scanGradient;
    ctx.fillRect(0, scanlineY - 35, width, 70);

    for (let i = 0; i < nodes.length; i++) {
      const n = nodes[i];
      n.x += n.vx;
      n.y += n.vy;

      if (n.x < 0 || n.x > width) n.vx *= -1;
      if (n.y < 0 || n.y > height) n.vy *= -1;

      if (mouse.active) {
        const dx = mouse.x - n.x;
        const dy = mouse.y - n.y;
        const dist = Math.hypot(dx, dy);
        if (dist < 130) {
          n.x += dx * 0.012;
          n.y += dy * 0.012;
        }
      }

      ctx.beginPath();
      ctx.arc(n.x, n.y, n.radius, 0, Math.PI * 2);
      ctx.fillStyle = n.color;
      ctx.fill();

      for (let j = i + 1; j < nodes.length; j++) {
        const n2 = nodes[j];
        const dist = Math.hypot(n.x - n2.x, n.y - n2.y);
        if (dist < 110) {
          const alpha = (1 - dist / 110) * 0.22;
          ctx.beginPath();
          ctx.moveTo(n.x, n.y);
          ctx.lineTo(n2.x, n2.y);
          ctx.strokeStyle = `rgba(223, 202, 167, ${alpha})`;
          ctx.lineWidth = 0.8;
          ctx.stroke();
        }
      }
    }

    requestAnimationFrame(render);
  }

  requestAnimationFrame(render);
}

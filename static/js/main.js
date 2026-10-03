// ---------------------------------------------------------------
// Pure vanilla JS. No build step, no framework — just DOM wiring
// for the interactive bits of the UI (buttons, toggles, dropzones).
// The actual application logic all lives server-side in Flask.
// ---------------------------------------------------------------

document.addEventListener("DOMContentLoaded", () => {
  initPasswordToggles();
  initRoleCardSelect();
  initDropzones();
  initTabs();
  initFlashAutoHide();
});

/** Eye icon buttons that flip a password field to type="text". */
function initPasswordToggles() {
  document.querySelectorAll(".toggle-visibility").forEach((btn) => {
    btn.addEventListener("click", () => {
      const targetId = btn.getAttribute("data-target");
      const input = document.getElementById(targetId);
      if (!input) return;
      const showing = input.type === "text";
      input.type = showing ? "password" : "text";
      btn.textContent = showing ? "\u{1F441}" : "\u{1F576}"; // eye / hidden-eye
    });
  });
}

/** Register page: clicking a role card selects its radio + highlights it,
 * and shows/hides the "Academic Information" section for students only. */
function initRoleCardSelect() {
  const cards = document.querySelectorAll(".role-card");
  if (!cards.length) return;

  const academicSection = document.getElementById("academic-info-section");
  const companySection = document.getElementById("company-info-section");

  function applyVisibility(role) {
    if (academicSection) academicSection.style.display = role === "student" ? "" : "none";
    if (companySection) companySection.style.display = role === "partner" ? "" : "none";
  }

  cards.forEach((card) => {
    card.addEventListener("click", () => {
      cards.forEach((c) => c.classList.remove("selected"));
      card.classList.add("selected");
      const radio = card.querySelector("input[type=radio]");
      if (radio) {
        radio.checked = true;
        applyVisibility(radio.value);
      }
    });
  });

  const checked = document.querySelector(".role-card input[type=radio]:checked");
  applyVisibility(checked ? checked.value : "student");
}

/** Drag-and-drop file upload zones. Falls back to a normal <input type=file>
 * click when the user clicks "Browse Files" instead of dragging. */
function initDropzones() {
  document.querySelectorAll(".dropzone").forEach((zone) => {
    const input = zone.querySelector("input[type=file]");
    const browseBtn = zone.querySelector(".browse-btn");
    const chosenLabel = zone.querySelector(".file-chosen");

    if (!input) return;

    if (browseBtn) {
      browseBtn.addEventListener("click", (e) => {
        e.preventDefault();
        input.click();
      });
    }

    zone.addEventListener("click", (e) => {
      if (e.target === zone || e.target.closest(".dz-icon") || e.target.closest("p")) {
        input.click();
      }
    });

    ["dragenter", "dragover"].forEach((evt) =>
      zone.addEventListener(evt, (e) => {
        e.preventDefault();
        zone.classList.add("dragover");
      })
    );

    ["dragleave", "drop"].forEach((evt) =>
      zone.addEventListener(evt, (e) => {
        e.preventDefault();
        zone.classList.remove("dragover");
      })
    );

    zone.addEventListener("drop", (e) => {
      if (e.dataTransfer.files.length) {
        input.files = e.dataTransfer.files;
        updateChosenLabel();
      }
    });

    input.addEventListener("change", updateChosenLabel);

    function updateChosenLabel() {
      if (chosenLabel && input.files.length) {
        chosenLabel.textContent = `Selected: ${input.files[0].name}`;
      }
    }
  });
}

/** Simple tab switcher: any [data-tabs] container with [data-tab-btn] /
 * [data-tab-panel] pairs sharing the same value. */
function initTabs() {
  document.querySelectorAll("[data-tabs]").forEach((group) => {
    const buttons = group.querySelectorAll("[data-tab-btn]");
    const panels = group.querySelectorAll("[data-tab-panel]");

    buttons.forEach((btn) => {
      btn.addEventListener("click", () => {
        const target = btn.getAttribute("data-tab-btn");
        buttons.forEach((b) => b.classList.remove("active"));
        panels.forEach((p) => (p.style.display = "none"));
        btn.classList.add("active");
        const panel = group.querySelector(`[data-tab-panel="${target}"]`);
        if (panel) panel.style.display = "";
      });
    });
  });
}

/** Auto-dismiss flash messages after a few seconds. */
function initFlashAutoHide() {
  document.querySelectorAll(".flash").forEach((el) => {
    setTimeout(() => {
      el.style.transition = "opacity .4s ease";
      el.style.opacity = "0";
      setTimeout(() => el.remove(), 400);
    }, 5000);
  });
}

/** Add-skill chip input on the student profile page. Adds the chip to the
 * DOM immediately for responsiveness; the form still submits to Flask. */
function addSkillChipPreview(inputId) {
  const input = document.getElementById(inputId);
  if (!input || !input.value.trim()) return;
  const list = document.getElementById("skills-chip-list");
  const chip = document.createElement("span");
  chip.className = "chip";
  chip.textContent = input.value.trim();
  list.appendChild(chip);
  input.value = "";
}

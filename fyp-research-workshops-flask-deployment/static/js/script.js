"use strict";

const menuToggle = document.querySelector(".menu-toggle");
const primaryNav = document.querySelector(".primary-nav");

function closeMenu() {
  menuToggle.setAttribute("aria-expanded", "false");
  menuToggle.setAttribute("aria-label", "Open navigation");
  primaryNav.classList.remove("is-open");
  document.body.classList.remove("menu-open");
}

menuToggle.addEventListener("click", () => {
  const isOpen = menuToggle.getAttribute("aria-expanded") === "true";
  menuToggle.setAttribute("aria-expanded", String(!isOpen));
  menuToggle.setAttribute("aria-label", isOpen ? "Open navigation" : "Close navigation");
  primaryNav.classList.toggle("is-open", !isOpen);
  document.body.classList.toggle("menu-open", !isOpen);
});

primaryNav.addEventListener("click", (event) => {
  if (event.target.matches("a")) closeMenu();
});

window.addEventListener("resize", () => {
  if (window.innerWidth > 900) closeMenu();
});

const filterButtons = document.querySelectorAll(".filter-button");
const workshopCards = document.querySelectorAll(".workshop-card");

filterButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const selected = button.dataset.filter;
    filterButtons.forEach((item) => {
      const active = item === button;
      item.classList.toggle("is-active", active);
      item.setAttribute("aria-pressed", String(active));
    });
    workshopCards.forEach((card) => {
      card.hidden = selected !== "all" && card.dataset.category !== selected;
    });
  });
});

const workshopData = window.WORKSHOP_DATA || {};
let activeWorkshopSlug = "";

const dialog = document.querySelector("#workshop-dialog");
const dialogTitle = document.querySelector("#dialog-title");
const dialogCategory = document.querySelector("#dialog-category");
const dialogDescription = document.querySelector("#dialog-description");
const dialogOutcomes = document.querySelector("#dialog-outcomes");

document.querySelectorAll(".details-button").forEach((button) => {
  button.addEventListener("click", () => {
    const workshop = workshopData[button.dataset.workshop];
    activeWorkshopSlug = button.dataset.workshop;
    dialogCategory.textContent = `${workshop.category} | Programme preview`;
    dialogTitle.textContent = workshop.title;
    dialogDescription.textContent = workshop.description;
    dialogOutcomes.replaceChildren(...workshop.outcomes.map((outcome) => {
      const item = document.createElement("li");
      item.textContent = outcome;
      return item;
    }));
    dialog.showModal();
  });
});

document.querySelector(".dialog-close").addEventListener("click", () => dialog.close());
dialog.addEventListener("click", (event) => {
  if (event.target === dialog) dialog.close();
});
document.querySelector(".dialog-register").addEventListener("click", () => {
  const select = document.querySelector("#workshop-select");
  select.value = activeWorkshopSlug;
  dialog.close();
  document.querySelector("#register").scrollIntoView({ behavior: "smooth" });
  window.setTimeout(() => select.focus(), 450);
});

const form = document.querySelector("#interest-form");
const fullName = document.querySelector("#full-name");
const email = document.querySelector("#email");
const workshopSelect = document.querySelector("#workshop-select");
const consent = document.querySelector("#demo-consent");
const message = document.querySelector("#message");
const characterCount = document.querySelector("#character-count");
const feedback = document.querySelector("#form-feedback");
const submitButton = form.querySelector("button[type='submit']");
const csrfToken = document.querySelector("meta[name='csrf-token']").content;

message.addEventListener("input", () => {
  characterCount.textContent = String(message.value.length);
});

function showError(field, messageText) {
  const error = document.querySelector(`#${field.getAttribute("aria-describedby")}`);
  field.classList.add("invalid");
  field.setAttribute("aria-invalid", "true");
  if (error) error.textContent = messageText;
}

function clearError(field) {
  const error = document.querySelector(`#${field.getAttribute("aria-describedby")}`);
  field.classList.remove("invalid");
  field.removeAttribute("aria-invalid");
  if (error && error.classList.contains("error")) error.textContent = "";
}

[fullName, email, workshopSelect].forEach((field) => {
  field.addEventListener("input", () => clearError(field));
  field.addEventListener("change", () => clearError(field));
});
consent.addEventListener("change", () => {
  consent.removeAttribute("aria-invalid");
  document.querySelector("#consent-error").textContent = "";
});

function showFeedback(messageText, isError = false) {
  feedback.textContent = messageText;
  feedback.classList.toggle("is-error", isError);
  feedback.classList.add("is-visible");
  feedback.focus();
}

function applyServerErrors(errors = {}) {
  const fieldMap = {
    fullName,
    email,
    workshop: workshopSelect,
    demoConsent: consent
  };
  Object.entries(errors).forEach(([name, messageText]) => {
    const field = fieldMap[name];
    if (field === consent) {
      consent.setAttribute("aria-invalid", "true");
      document.querySelector("#consent-error").textContent = messageText;
    } else if (field) {
      showError(field, messageText);
    }
  });
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  feedback.classList.remove("is-visible", "is-error");

  let valid = true;
  if (fullName.value.trim().length < 2) {
    showError(fullName, "Enter your full name.");
    valid = false;
  }
  if (!email.validity.valid || !email.value.trim()) {
    showError(email, "Enter a valid email address.");
    valid = false;
  }
  if (!workshopSelect.value) {
    showError(workshopSelect, "Choose a workshop.");
    valid = false;
  }
  if (!consent.checked) {
    consent.setAttribute("aria-invalid", "true");
    document.querySelector("#consent-error").textContent = "Confirm that you understand how this demonstration stores your entry.";
    valid = false;
  }

  if (!valid) {
    const firstInvalid = form.querySelector("[aria-invalid='true']");
    firstInvalid?.focus();
    return;
  }

  const payload = {
    requestType: form.querySelector("input[name='requestType']:checked").value,
    fullName: fullName.value.trim(),
    email: email.value.trim(),
    workshop: workshopSelect.value,
    message: message.value.trim(),
    demoConsent: consent.checked
  };

  submitButton.disabled = true;
  submitButton.textContent = "Saving...";

  try {
    const response = await fetch("/api/registrations", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken
      },
      body: JSON.stringify(payload)
    });
    const result = await response.json();

    if (!response.ok) {
      applyServerErrors(result.errors);
      showFeedback(result.message || "The entry could not be saved. Please try again.", true);
      return;
    }

    showFeedback(`${result.message} Reference: ${result.reference}. Workshop: ${result.workshop}.`);
    form.reset();
    characterCount.textContent = "0";
  } catch (_error) {
    showFeedback("The service is currently unavailable. Check your connection and try again.", true);
  } finally {
    submitButton.disabled = false;
    submitButton.innerHTML = `Submit entry <span aria-hidden="true">&rarr;</span>`;
  }
});

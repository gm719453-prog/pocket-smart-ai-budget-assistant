/**
 * PocketSmart AI - Authentication Interactions (auth.js)
 */

document.addEventListener("DOMContentLoaded", () => {
  // 1. Password Visibility Toggle
  const toggleButtons = document.querySelectorAll(".btn-toggle-password");
  toggleButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const input = btn.previousElementSibling;
      if (input && (input.type === "password" || input.type === "text")) {
        const isPassword = input.type === "password";
        input.type = isPassword ? "text" : "password";
        const icon = btn.querySelector("i");
        if (icon) {
          icon.className = isPassword ? "fas fa-eye-slash" : "fas fa-eye";
        }
      }
    });
  });

  // 2. Auth Form Submission & Loading State
  const authForm = document.getElementById("authForm");
  if (authForm) {
    authForm.addEventListener("submit", (e) => {
      const submitBtn = authForm.querySelector(".btn-auth-submit");
      const emailInput = authForm.querySelector("input[name='email']");
      const passwordInput = authForm.querySelector("input[name='password']");
      const confirmInput = authForm.querySelector("input[name='confirm_password']");

      // Validate Email
      if (emailInput) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(emailInput.value.trim())) {
          e.preventDefault();
          window.showToast("Please enter a valid email address.", "danger");
          emailInput.focus();
          return;
        }
      }

      // Validate Password length if signing up
      if (passwordInput && confirmInput) {
        if (passwordInput.value.length < 6) {
          e.preventDefault();
          window.showToast("Password must be at least 6 characters long.", "danger");
          passwordInput.focus();
          return;
        }
        if (passwordInput.value !== confirmInput.value) {
          e.preventDefault();
          window.showToast("Passwords do not match.", "danger");
          confirmInput.focus();
          return;
        }
      }

      // Show Loading State
      if (submitBtn) {
        submitBtn.disabled = true;
        const originalText = submitBtn.innerHTML;
        submitBtn.setAttribute("data-original", originalText);
        submitBtn.innerHTML = `
          <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
          Please wait...
        `;
      }
    });
  }
});

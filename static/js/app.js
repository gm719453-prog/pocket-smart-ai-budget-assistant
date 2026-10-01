/**
 * PocketSmart AI - Global Application Scripts (app.js)
 */

document.addEventListener("DOMContentLoaded", () => {
  // 1. Mobile Sidebar Toggle
  const toggleBtn = document.getElementById("sidebarToggleBtn");
  const sidebar = document.getElementById("appSidebar");
  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener("click", () => {
      sidebar.classList.toggle("show-sidebar");
    });

    // Close when clicking outside on mobile
    document.addEventListener("click", (e) => {
      if (window.innerWidth <= 992 && !sidebar.contains(e.target) && !toggleBtn.contains(e.target)) {
        sidebar.classList.remove("show-sidebar");
      }
    });
  }

  // 2. Global Toast Notification Helper
  window.showToast = function(message, type = "info") {
    let container = document.querySelector(".ps-toast-container");
    if (!container) {
      container = document.createElement("div");
      container.className = "ps-toast-container";
      document.body.appendChild(container);
    }

    const toast = document.createElement("div");
    toast.className = `ps-toast alert-${type}-custom`;
    
    let iconClass = "fa-info-circle";
    if (type === "success") iconClass = "fa-check-circle";
    if (type === "danger" || type === "error") iconClass = "fa-exclamation-triangle";
    if (type === "warning") iconClass = "fa-exclamation-circle";

    toast.innerHTML = `
      <i class="fas ${iconClass} me-2"></i>
      <span style="flex:1;">${message}</span>
      <button type="button" class="btn-close btn-close-white ms-2" style="font-size: 0.75rem;" aria-label="Close"></button>
    `;

    toast.querySelector("button").addEventListener("click", () => {
      toast.remove();
    });

    container.appendChild(toast);

    // Auto remove after 4.5 seconds
    setTimeout(() => {
      toast.style.transition = "opacity 0.4s ease, transform 0.4s ease";
      toast.style.opacity = "0";
      toast.style.transform = "translateX(50px)";
      setTimeout(() => toast.remove(), 400);
    }, 4500);
  };

  // 3. Theme Toggle Initialization
  const themeSwitchBtn = document.getElementById("themeToggleBtn");
  if (themeSwitchBtn) {
    themeSwitchBtn.addEventListener("click", () => {
      const currentTheme = document.documentElement.getAttribute("data-theme") || "dark";
      const newTheme = currentTheme === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", newTheme);
      localStorage.setItem("ps_theme", newTheme);
      
      const icon = themeSwitchBtn.querySelector("i");
      if (icon) {
        icon.className = newTheme === "dark" ? "fas fa-moon" : "fas fa-sun";
      }
    });
  }

  // Restore saved theme
  const savedTheme = localStorage.getItem("ps_theme");
  if (savedTheme) {
    document.documentElement.setAttribute("data-theme", savedTheme);
  }
});

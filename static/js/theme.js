/**
 * Theme management — dark/light mode.
 * Reads saved theme from localStorage (set by the settings page),
 * falls back to system preference on first visit.
 */

(function () {
  const htmlEl = document.getElementById("html-root") || document.documentElement;

  function getStoredTheme() {
    return localStorage.getItem("theme");
  }

  function getSystemTheme() {
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }

  function applyTheme(theme) {
    if (theme === "dark") {
      htmlEl.classList.add("dark");
      htmlEl.classList.remove("light");
    } else {
      htmlEl.classList.remove("dark");
      htmlEl.classList.add("light");
    }
    localStorage.setItem("theme", theme);
    updateToggleIcon(theme);
  }

  function updateToggleIcon(theme) {
    const sunIcon  = document.getElementById("theme-icon-sun");
    const moonIcon = document.getElementById("theme-icon-moon");
    if (!sunIcon || !moonIcon) return;
    if (theme === "dark") {
      sunIcon.classList.remove("hidden");
      moonIcon.classList.add("hidden");
    } else {
      sunIcon.classList.add("hidden");
      moonIcon.classList.remove("hidden");
    }
  }

  function toggleTheme() {
    const current = htmlEl.classList.contains("dark") ? "dark" : "light";
    applyTheme(current === "dark" ? "light" : "dark");
  }

  // Expose globals
  window.applyTheme  = applyTheme;
  window.toggleTheme = toggleTheme;

  // Apply theme immediately on page load (before DOM ready to avoid flicker)
  const stored = getStoredTheme();
  applyTheme(stored || getSystemTheme());
})();

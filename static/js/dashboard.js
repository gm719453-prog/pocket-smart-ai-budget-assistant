/**
 * PocketSmart AI - Dashboard Interactive Scripts (dashboard.js)
 */

document.addEventListener("DOMContentLoaded", () => {
  // 1. Count-up Animation for Metric Numbers
  const countUpElements = document.querySelectorAll("[data-countup]");
  
  countUpElements.forEach(el => {
    const target = parseFloat(el.getAttribute("data-countup")) || 0;
    const prefix = el.getAttribute("data-prefix") || "";
    const suffix = el.getAttribute("data-suffix") || "";
    const duration = 1200; // ms
    const startTime = performance.now();

    function updateCount(currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      
      // Ease out cubic
      const easeProgress = 1 - Math.pow(1 - progress, 3);
      const currentVal = target * easeProgress;

      el.textContent = `${prefix}${currentVal.toLocaleString('en-IN', { maximumFractionDigits: 0 })}${suffix}`;

      if (progress < 1) {
        requestAnimationFrame(updateCount);
      } else {
        el.textContent = `${prefix}${target.toLocaleString('en-IN', { maximumFractionDigits: 2 })}${suffix}`;
      }
    }

    requestAnimationFrame(updateCount);
  });

  // 2. Animate Progress Bars
  const progressBars = document.querySelectorAll(".progress-fill[data-progress-width]");
  setTimeout(() => {
    progressBars.forEach(bar => {
      const width = bar.getAttribute("data-progress-width");
      bar.style.width = `${Math.min(parseFloat(width) || 0, 100)}%`;
    });
  }, 150);
});

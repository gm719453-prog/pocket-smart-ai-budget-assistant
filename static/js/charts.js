/**
 * PocketSmart AI - Chart.js Visualizations (charts.js)
 */

document.addEventListener("DOMContentLoaded", () => {
  // Fetch chart data from API
  fetch("/api/chart-data")
    .then(res => res.json())
    .then(data => {
      if (!data.success) return;
      const currency = data.currency || "₹";

      // Common chart options
      const textColor = getComputedStyle(document.documentElement).getPropertyValue('--text-secondary').trim() || "#94a3b8";
      const borderColor = getComputedStyle(document.documentElement).getPropertyValue('--border-color').trim() || "rgba(255,255,255,0.08)";
      
      const chartColors = [
        "#f59e0b", // Food - Amber
        "#3b82f6", // Travel - Blue
        "#ec4899", // Shopping - Pink
        "#8b5cf6", // Education - Purple
        "#ef4444", // Bills - Red
        "#10b981", // Entertainment - Emerald
        "#06b6d4", // Health - Cyan
        "#9ca3af"  // Other - Gray
      ];

      // 1. Category Doughnut Chart
      const catCanvas = document.getElementById("categoryChart");
      if (catCanvas && data.category_chart.labels.length > 0) {
        new Chart(catCanvas, {
          type: "doughnut",
          data: {
            labels: data.category_chart.labels,
            datasets: [{
              data: data.category_chart.data,
              backgroundColor: chartColors.slice(0, data.category_chart.labels.length),
              borderWidth: 2,
              borderColor: "transparent"
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                position: "bottom",
                labels: { color: textColor, font: { family: "Inter", size: 12 }, padding: 16 }
              },
              tooltip: {
                callbacks: {
                  label: function(ctx) {
                    return ` ${ctx.label}: ${currency}${ctx.raw.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`;
                  }
                }
              }
            },
            cutout: "68%"
          }
        });
      } else if (catCanvas) {
        const parent = catCanvas.parentElement;
        parent.innerHTML = `<div class="d-flex align-items-center justify-content-center h-100 text-muted" style="font-size: 0.9rem;"><i class="fas fa-chart-pie me-2"></i>No expense category records yet</div>`;
      }

      // 2. Monthly Spending Bar / Line Chart
      const trendCanvas = document.getElementById("monthlyTrendChart");
      if (trendCanvas && data.monthly_trend.labels.length > 0) {
        new Chart(trendCanvas, {
          type: "bar",
          data: {
            labels: data.monthly_trend.labels,
            datasets: [{
              label: "Total Spending",
              data: data.monthly_trend.data,
              backgroundColor: "rgba(99, 102, 241, 0.4)",
              borderColor: "#6366f1",
              borderWidth: 2,
              borderRadius: 8,
              borderSkipped: false
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
              x: {
                grid: { display: false },
                ticks: { color: textColor, font: { family: "Inter" } }
              },
              y: {
                grid: { color: borderColor },
                ticks: {
                  color: textColor,
                  font: { family: "Inter" },
                  callback: function(val) { return currency + val.toLocaleString('en-IN'); }
                }
              }
            },
            plugins: {
              legend: { display: false },
              tooltip: {
                callbacks: {
                  label: function(ctx) {
                    return ` Spent: ${currency}${ctx.raw.toLocaleString('en-IN')}`;
                  }
                }
              }
            }
          }
        });
      }

      // 3. Budget vs Spent Comparison
      const budgetCanvas = document.getElementById("budgetComparisonChart");
      if (budgetCanvas && data.budget_vs_spent.labels.length > 0) {
        new Chart(budgetCanvas, {
          type: "bar",
          data: {
            labels: data.budget_vs_spent.labels,
            datasets: [
              {
                label: "Budget",
                data: data.budget_vs_spent.budgets,
                backgroundColor: "rgba(16, 185, 129, 0.6)",
                borderRadius: 6
              },
              {
                label: "Spent",
                data: data.budget_vs_spent.spent,
                backgroundColor: "rgba(239, 68, 68, 0.6)",
                borderRadius: 6
              }
            ]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
              x: { grid: { display: false }, ticks: { color: textColor } },
              y: {
                grid: { color: borderColor },
                ticks: {
                  color: textColor,
                  callback: function(v) { return currency + v; }
                }
              }
            },
            plugins: {
              legend: {
                position: "top",
                labels: { color: textColor, font: { family: "Inter" } }
              }
            }
          }
        });
      }
    })
    .catch(err => {
      console.warn("Chart data load notice:", err);
    });
});

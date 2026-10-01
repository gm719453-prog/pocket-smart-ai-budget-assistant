/**
 * PocketSmart AI - Expenses Management Scripts (expenses.js)
 */

document.addEventListener("DOMContentLoaded", () => {
  // 1. Client-side Search / Filter for Expense Table
  const searchInput = document.getElementById("expenseSearchInput");
  const categoryFilter = document.getElementById("categoryFilterSelect");
  const tableRows = document.querySelectorAll(".expense-table-row");

  function filterExpenses() {
    const searchTerm = searchInput ? searchInput.value.toLowerCase().trim() : "";
    const selectedCategory = categoryFilter ? categoryFilter.value : "All";

    tableRows.forEach(row => {
      const desc = row.getAttribute("data-description") || "";
      const cat = row.getAttribute("data-category") || "";

      const matchesSearch = !searchTerm || desc.includes(searchTerm) || cat.toLowerCase().includes(searchTerm);
      const matchesCategory = (selectedCategory === "All" || !selectedCategory) || (cat === selectedCategory);

      if (matchesSearch && matchesCategory) {
        row.style.display = "";
      } else {
        row.style.display = "none";
      }
    });
  }

  if (searchInput) searchInput.addEventListener("input", filterExpenses);
  if (categoryFilter) categoryFilter.addEventListener("change", filterExpenses);

  // 2. Delete Expense Modal Setup
  const deleteModal = document.getElementById("deleteExpenseModal");
  if (deleteModal) {
    deleteModal.addEventListener("show.bs.modal", (event) => {
      const button = event.relatedTarget;
      const expenseId = button.getAttribute("data-expense-id");
      const expenseDesc = button.getAttribute("data-expense-desc");
      const expenseAmount = button.getAttribute("data-expense-amount");

      const form = document.getElementById("deleteExpenseForm");
      if (form) {
        form.action = `/expenses/delete/${expenseId}`;
      }

      const descEl = document.getElementById("deleteExpenseDesc");
      if (descEl) {
        descEl.textContent = `${expenseDesc} (${expenseAmount})`;
      }
    });
  }
});

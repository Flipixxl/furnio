(function () {
  "use strict";

  // ---------- Header shadow on scroll ----------
  const header = document.getElementById("siteHeader");
  if (header) {
    const onScroll = () => {
      header.style.boxShadow = window.scrollY > 8 ? "0 4px 20px rgba(43,38,32,0.08)" : "none";
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
  }

  // ---------- Mobile menu ----------
  const burger = document.getElementById("burgerBtn");
  const mobileMenu = document.getElementById("mobileMenu");
  if (burger && mobileMenu) {
    burger.addEventListener("click", () => {
      const open = mobileMenu.classList.toggle("open");
      burger.setAttribute("aria-expanded", String(open));
    });
  }

  // ---------- Filters panel (mobile) ----------
  const filtersPanel = document.getElementById("filtersPanel");
  const filtersToggle = document.getElementById("filtersToggle");
  const filtersClose = document.getElementById("filtersClose");
  if (filtersPanel) {
    const closeFilters = () => filtersPanel.classList.remove("open");
    if (filtersToggle) filtersToggle.addEventListener("click", () => filtersPanel.classList.add("open"));
    if (filtersClose) filtersClose.addEventListener("click", closeFilters);
    document.addEventListener("click", (e) => {
      if (filtersPanel.classList.contains("open") &&
          !filtersPanel.contains(e.target) &&
          !(filtersToggle && filtersToggle.contains(e.target))) {
        closeFilters();
      }
    });
  }

  // ---------- Toast ----------
  const toast = document.getElementById("toast");
  let toastTimer = null;
  function showToast(message) {
    if (!toast) return;
    toast.textContent = message;
    toast.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove("show"), 2600);
  }

  // ---------- Cart badge ----------
  const cartCount = document.getElementById("cartCount");
  function updateCartCount(n) {
    if (!cartCount) return;
    cartCount.textContent = n;
    cartCount.classList.add("bump");
    setTimeout(() => cartCount.classList.remove("bump"), 300);
  }

  // ---------- Quantity steppers ----------
  document.querySelectorAll(".qty-stepper").forEach((stepper) => {
    const minus = stepper.querySelector("[data-qty-minus]");
    const plus = stepper.querySelector("[data-qty-plus]");
    const input = stepper.querySelector("[data-qty-input]");
    if (!minus || !plus || !input) return;

    minus.addEventListener("click", () => {
      const val = parseInt(input.value, 10) || 1;
      if (val > 1) input.value = val - 1;
    });
    plus.addEventListener("click", () => {
      const val = parseInt(input.value, 10) || 1;
      const max = parseInt(input.max, 10) || 99;
      if (val < max) input.value = val + 1;
    });
  });

  // ---------- Add to cart via AJAX ----------
  document.querySelectorAll("[data-add-form]").forEach((form) => {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const button = form.querySelector("button[type=submit]");
      if (button && button.disabled) return;

      try {
        const body = new FormData(form);
        const res = await fetch(form.action, {
          method: "POST",
          headers: { "X-Requested-With": "fetch" },
          body,
        });
        if (!res.ok) throw new Error("bad response");
        const data = await res.json();
        if (data.ok) {
          updateCartCount(data.cart_count);
          showToast("Товар добавлен в корзину 🛒");
        }
      } catch (err) {
        showToast("Не удалось добавить товар. Попробуйте ещё раз.");
      }
    });
  });

  // ---------- Cart badge bump animation ----------
  const style = document.createElement("style");
  style.textContent = `
    .cart-count.bump { animation: cartBump 0.3s ease; }
    @keyframes cartBump {
      0% { transform: scale(1); }
      50% { transform: scale(1.35); }
      100% { transform: scale(1); }
    }
  `;
  document.head.appendChild(style);
})();
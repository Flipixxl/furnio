(function () {
  "use strict";

  // ---------- Header shadow on scroll ----------
  const header = document.getElementById("siteHeader");
  if (header) {
    const onScroll = () => {
      header.style.boxShadow = window.scrollY > 8 ? "0 4px 20px rgba(43,38,32,0.1)" : "none";
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

  // ---------- Reveal on scroll ----------
  const revealEls = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("in");
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.08, rootMargin: "0px 0px -40px 0px" });
    revealEls.forEach((el) => io.observe(el));
  } else {
    revealEls.forEach((el) => el.classList.add("in"));
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
  async function addToCart(form, message) {
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
        showToast(message || "Товар добавлен в корзину 🛒");
      }
    } catch (err) {
      showToast("Не удалось добавить товар. Попробуйте ещё раз.");
    }
  }

  document.querySelectorAll("[data-add-form]").forEach((form) => {
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      addToCart(form);
    });
  });

  // ---------- Quick view modal ----------
  const modal = document.getElementById("qvModal");
  if (modal) {
    const setText = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.textContent = val;
    };

    document.querySelectorAll("[data-quick-view]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const card = btn.closest(".product-card");
        if (!card) return;

        const d = card.dataset;
        setText("qvTitle", d.qvName);
        setText("qvCategory", d.qvCat);
        setText("qvPrice", Number(d.qvPrice).toLocaleString("ru-RU") + " ₽");
        setText("qvOld", d.qvOld ? Number(d.qvOld).toLocaleString("ru-RU") + " ₽" : "");
        setText("qvDesc", d.qvDesc);
        setText("qvMaterial", d.qvMat);
        setText("qvDims", d.qvDims);
        setText("qvWarranty", d.qvWar);

        const img = document.getElementById("qvImage");
        img.src = d.qvImg;
        img.alt = d.qvName;

        const link = document.getElementById("qvLink");
        link.href = d.qvUrl;

        const form = document.getElementById("qvForm");
        form.action = "/cart/add/" + d.qvId;

        modal.classList.add("open");
        modal.setAttribute("aria-hidden", "false");
        document.body.style.overflow = "hidden";
      });
    });

    const closeQv = () => {
      modal.classList.remove("open");
      modal.setAttribute("aria-hidden", "true");
      document.body.style.overflow = "";
    };

    modal.querySelectorAll("[data-qv-close]").forEach((el) => {
      el.addEventListener("click", closeQv);
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && modal.classList.contains("open")) closeQv();
    });
  }

  // ---------- View toggle (grid / list) ----------
  const grid = document.getElementById("productsGrid");
  const viewBtns = document.querySelectorAll(".view-btn");
  if (grid && viewBtns.length) {
    viewBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        const view = btn.dataset.view;
        grid.dataset.view = view;
        viewBtns.forEach((b) => b.classList.toggle("active", b === btn));
      });
    });
  }

  // ---------- Newsletter ----------
  const newsletter = document.getElementById("newsletterForm");
  if (newsletter) {
    newsletter.addEventListener("submit", (e) => {
      e.preventDefault();
      const input = newsletter.querySelector("input");
      if (input && input.value) {
        input.value = "";
        showToast("Спасибо! Вы подписаны на рассылку ✉️");
      }
    });
  }

  // ---------- Promo countdown ----------
  const timer = document.querySelector("[data-timer]");
  if (timer) {
    const key = "furnio_promo_end";
    let end = localStorage.getItem(key);
    if (!end) {
      end = Date.now() + 30 * 24 * 3600 * 1000;
      localStorage.setItem(key, end);
    }
    end = Number(end);
    const daysEl = timer.querySelector("[data-timer-days]");
    const hoursEl = timer.querySelector("[data-timer-hours]");
    const minsEl = timer.querySelector("[data-timer-mins]");
    const pad = (n) => String(n).padStart(2, "0");

    const tick = () => {
      let diff = Math.max(0, end - Date.now());
      const days = Math.floor(diff / (24 * 3600 * 1000));
      diff -= days * 24 * 3600 * 1000;
      const hours = Math.floor(diff / (3600 * 1000));
      diff -= hours * 3600 * 1000;
      const mins = Math.floor(diff / (60 * 1000));
      if (daysEl) daysEl.textContent = pad(days);
      if (hoursEl) hoursEl.textContent = pad(hours);
      if (minsEl) minsEl.textContent = pad(mins);
    };
    tick();
    setInterval(tick, 30000);
  }

  // ---------- Cart badge bump animation ----------
  const style = document.createElement("style");
  style.textContent = `
    .cart-count.bump { animation: cartBump 0.3s ease; }
    @keyframes cartBump {
      0% { transform: scale(1); }
      50% { transform: scale(1.4); }
      100% { transform: scale(1); }
    }
  `;
  document.head.appendChild(style);
})();
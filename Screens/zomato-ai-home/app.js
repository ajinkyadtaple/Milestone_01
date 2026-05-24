/**
 * Lightweight interactions for the Zomato AI home screen mockup.
 */
(function () {
  const pills = document.querySelectorAll(".cuisine-pill");
  const cuisineInput = document.getElementById("cuisine");
  const locationSelect = document.getElementById("location");
  const trendingTitle = document.getElementById("trending-title");
  const sessionEl = document.getElementById("session-id");
  const form = document.getElementById("search-form");
  const newSessionBtn = document.getElementById("btn-new-session");

  function randomSessionId() {
    return "AI-" + Math.floor(1000 + Math.random() * 9000);
  }

  pills.forEach((pill) => {
    pill.addEventListener("click", () => {
      pills.forEach((p) => p.classList.remove("active"));
      pill.classList.add("active");
      if (cuisineInput) cuisineInput.value = pill.dataset.cuisine || "";
    });
  });

  function updateTrendingLabel() {
    if (!locationSelect || !trendingTitle) return;
    const area = locationSelect.value || "Bangalore";
    trendingTitle.textContent = "Trending in " + area;
  }

  locationSelect?.addEventListener("change", updateTrendingLabel);

  newSessionBtn?.addEventListener("click", () => {
    if (sessionEl) sessionEl.textContent = randomSessionId();
  });

  form?.addEventListener("submit", (e) => {
    e.preventDefault();
    const btn = form.querySelector(".btn-primary");
    if (!btn) return;
    const original = btn.innerHTML;
    btn.innerHTML = '<span aria-hidden="true">⏳</span> Finding matches…';
    btn.disabled = true;
    setTimeout(() => {
      btn.innerHTML = original;
      btn.disabled = false;
    }, 1200);
  });

  document.getElementById("chat-fab")?.addEventListener("click", () => {
    alert("Chat panel — connect to Phase 3 /recommend API in production.");
  });

  updateTrendingLabel();
})();

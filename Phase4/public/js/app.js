/**
 * Phase 4 — Premium UI client for Phase 3 API
 */
(function () {
  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => document.querySelectorAll(sel);

  let sessionId = localStorage.getItem("zomato_session_id") || null;
  let budgetTier = "";
  let isLoading = false;

  const els = {
    form: $("#search-form"),
    budgetBtns: $$(".budget-btn"),
    budgetInput: $("#budget_tier"),
    welcome: $("#welcome-view"),
    loader: $("#loader-view"),
    progress: $("#progress-steps"),
    error: $("#error-view"),
    errorText: $("#error-text"),
    grid: $("#results-grid"),
    agentBar: $("#agent-bar"),
    agentText: $("#agent-text"),
    sessionBadge: $("#session-badge"),
    chatPanel: $("#chat-panel"),
    chatMessages: $("#chat-messages"),
    chatForm: $("#chat-form"),
    chatInput: $("#chat-input"),
    chatToggle: $("#chat-toggle"),
    newSessionBtn: $("#new-session-btn"),
    apiStatus: $("#api-status"),
  };

  function apiUrl(path) {
    return `${window.ZOMATO_CONFIG.apiBase}${path}`;
  }

  function escapeHTML(str) {
    if (!str) return "";
    return String(str).replace(
      /[&<>'"]/g,
      (tag) =>
        ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[tag] || tag)
    );
  }

  function setView(view) {
    els.welcome.classList.toggle("hidden", view !== "welcome");
    els.loader.classList.toggle("hidden", view !== "loading");
    els.error.classList.toggle("hidden", view !== "error");
    els.grid.classList.toggle("hidden", view !== "results");
    els.agentBar.classList.toggle("hidden", view === "welcome" || view === "loading");
  }

  function setProgress(step) {
    const items = els.progress.querySelectorAll(".progress-step");
    items.forEach((el, i) => {
      el.classList.remove("active", "done");
      if (i < step) el.classList.add("done");
      if (i === step) el.classList.add("active");
    });
  }

  function updateSessionUI() {
    if (sessionId) {
      els.sessionBadge.textContent = `Session ${sessionId.slice(0, 8)}…`;
      els.sessionBadge.classList.remove("hidden");
    } else {
      els.sessionBadge.classList.add("hidden");
    }
  }

  function buildPayload(descriptionOnly = false) {
    const payload = { description: descriptionOnly ? els.chatInput.value.trim() : $("#description").value.trim() };
    if (sessionId) payload.session_id = sessionId;
    if (!descriptionOnly) {
      payload.location = $("#location").value;
      payload.cuisine = $("#cuisine").value.trim();
      payload.budget_tier = budgetTier;
      payload.min_rating = parseFloat($("#min_rating").value) || 0;
      const maxCost = parseInt($("#max_cost").value, 10);
      if (!Number.isNaN(maxCost) && maxCost > 0) payload.max_cost = maxCost;
    }
    return payload;
  }

  async function checkHealth() {
    try {
      const res = await fetch(apiUrl("/health"), { signal: AbortSignal.timeout(5000) });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const h = await res.json();
      els.apiStatus.textContent = `API online · ${h.records?.toLocaleString() ?? 0} restaurants`;
      els.apiStatus.classList.add("online");
      return true;
    } catch (e) {
      els.apiStatus.textContent = `API offline — start Phase 3 (${window.ZOMATO_CONFIG.apiBase})`;
      els.apiStatus.classList.remove("online");
      return false;
    }
  }

  function renderCards(recommendations) {
    els.grid.innerHTML = "";
    if (!recommendations?.length) {
      els.grid.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon">🔍</div>
          <h2>No matches</h2>
          <p>Try relaxing filters, another location, or describe what you want in the chat.</p>
        </div>`;
      return;
    }

    recommendations.forEach((item, index) => {
      let ratingClass = "";
      if (item.rating < 4 && item.rating >= 3) ratingClass = "low";
      else if (item.rating < 3) ratingClass = "poor";

      const tags = (item.cuisines || "")
        .split(",")
        .map((t) => t.trim())
        .filter(Boolean)
        .slice(0, 4);

      const tagHtml = tags
        .map((t) => `<span class="tag">${escapeHTML(t)}</span>`)
        .join("");
      const more =
        (item.cuisines || "").split(",").length > 4
          ? `<span class="tag tag-more">+more</span>`
          : "";

      els.grid.insertAdjacentHTML(
        "beforeend",
        `
        <article class="restaurant-card" data-rank="${index + 1}">
          <div class="card-image" aria-hidden="true">
            <span class="card-rank">#${index + 1}</span>
          </div>
          <div class="card-body">
            <div class="card-header">
              <h3 class="restaurant-title">${escapeHTML(item.name)}</h3>
              <div class="rating-badge ${ratingClass}">★ ${Number(item.rating).toFixed(1)}</div>
            </div>
            <div class="restaurant-meta">
              <span class="meta-item">📍 ${escapeHTML(item.location)}</span>
              <span class="meta-item">💰 ~₹${item.cost} for two</span>
            </div>
            <div class="tag-row">${tagHtml}${more}</div>
            <div class="ai-explanation">
              <p>${escapeHTML(item.explanation)}</p>
            </div>
          </div>
        </article>`
      );
    });
  }

  function appendChatMessage(role, text) {
    const div = document.createElement("div");
    div.className = `chat-bubble ${role}`;
    div.textContent = text;
    els.chatMessages.appendChild(div);
    els.chatMessages.scrollTop = els.chatMessages.scrollHeight;
  }

  function showAgentInfo(data) {
    const tools = (data.tools_used || []).join(" → ");
    els.agentText.textContent = data.message
      ? `${data.message}${tools ? ` · ${tools}` : ""}`
      : tools || "Recommendations ready.";
  }

  async function fetchRecommendations(payload, { fromChat = false } = {}) {
    if (isLoading) return;
    isLoading = true;

    setView("loading");
    setProgress(0);

    const stepTimer = [
      setTimeout(() => setProgress(1), 400),
      setTimeout(() => setProgress(2), 1200),
    ];

    try {
      const res = await fetch(apiUrl("/recommend"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errBody = await res.json().catch(() => ({}));
        throw new Error(errBody.detail || `Server error ${res.status}`);
      }

      setProgress(2);
      const data = await res.json();

      sessionId = data.session_id;
      localStorage.setItem("zomato_session_id", sessionId);
      updateSessionUI();

      if (fromChat && payload.description) {
        appendChatMessage("user", payload.description);
        appendChatMessage(
          "assistant",
          data.recommendations?.length
            ? `Found ${data.recommendations.length} picks. See cards above.`
            : data.message || "No results."
        );
        els.chatInput.value = "";
      }

      renderCards(data.recommendations);
      showAgentInfo(data);
      setView("results");
    } catch (err) {
      console.error(err);
      els.errorText.textContent =
        err.message ||
        `Cannot reach Phase 3 API at ${window.ZOMATO_CONFIG.apiBase}. Run: cd Phase3 && python -m src.main`;
      setView("error");
    } finally {
      stepTimer.forEach(clearTimeout);
      isLoading = false;
    }
  }

  // Budget tier toggles
  els.budgetBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      const selected = btn.classList.contains("active");
      els.budgetBtns.forEach((b) => b.classList.remove("active"));
      if (selected) {
        budgetTier = "";
        els.budgetInput.value = "";
      } else {
        btn.classList.add("active");
        budgetTier = btn.dataset.tier;
        els.budgetInput.value = budgetTier;
      }
    });
  });

  els.form.addEventListener("submit", (e) => {
    e.preventDefault();
    fetchRecommendations(buildPayload());
  });

  els.chatForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const text = els.chatInput.value.trim();
    if (!text) return;
    if (!sessionId) {
      appendChatMessage("assistant", "Run a search first to start a session.");
      return;
    }
    fetchRecommendations({ session_id: sessionId, description: text }, { fromChat: true });
  });

  els.chatToggle.addEventListener("click", () => {
    els.chatPanel.classList.toggle("open");
  });

  els.newSessionBtn.addEventListener("click", async () => {
    if (sessionId) {
      try {
        await fetch(apiUrl(`/session/${sessionId}`), { method: "DELETE" });
      } catch (_) {
        /* ignore */
      }
    }
    sessionId = null;
    localStorage.removeItem("zomato_session_id");
    els.chatMessages.innerHTML = "";
    updateSessionUI();
    setView("welcome");
    appendChatMessage("assistant", "New session. Adjust filters and search again.");
  });

  async function boot() {
    if (window.ZOMATO_CONFIG?.load) {
      await window.ZOMATO_CONFIG.load();
    }
    updateSessionUI();
    checkHealth();
    setInterval(checkHealth, 30000);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();

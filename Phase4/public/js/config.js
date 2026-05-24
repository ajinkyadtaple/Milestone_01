/**
 * Phase 3 API base URL — loaded from /runtime-config.json when possible.
 */
(function () {
  const params = new URLSearchParams(window.location.search);
  const fromQuery = params.get("api");
  const fromStorage = localStorage.getItem("zomato_api_base");
  const fallback = "http://127.0.0.1:8001";

  function resolveBase() {
    return (fromQuery || fromStorage || fallback).replace(/\/$/, "");
  }

  window.ZOMATO_CONFIG = {
    apiBase: resolveBase(),
    ready: false,
    async load() {
      if (fromQuery) {
        this.apiBase = fromQuery.replace(/\/$/, "");
        this.ready = true;
        return this.apiBase;
      }
      try {
        const res = await fetch("/runtime-config.json", { cache: "no-store" });
        if (res.ok) {
          const cfg = await res.json();
          if (cfg.apiBase) {
            this.apiBase = cfg.apiBase.replace(/\/$/, "");
            localStorage.setItem("zomato_api_base", this.apiBase);
          }
        }
      } catch (_) {
        /* use fallback */
      }
      this.ready = true;
      return this.apiBase;
    },
    setApiBase(url) {
      this.apiBase = url.replace(/\/$/, "");
      localStorage.setItem("zomato_api_base", this.apiBase);
    },
  };
})();

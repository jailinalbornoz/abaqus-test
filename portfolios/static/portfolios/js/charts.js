(function () {
  const fmtUSD = new Intl.NumberFormat("es-CL", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
  const fmtPct = new Intl.NumberFormat("es-CL", { style: "percent", maximumFractionDigits: 2 });

  let charts = { v: null, w: null, dd: null };
  let abortCtl = null;

  function setStatus(type, message) {
    const el = document.getElementById("statusArea");
    if (!el) return;
    if (!message) { el.innerHTML = ""; return; }
    el.innerHTML = `<div class="alert alert-${type} mb-0" role="alert">${escapeHtml(message)}</div>`;
  }

  function escapeHtml(str) {
    return String(str)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function destroyCharts() {
    Object.values(charts).forEach((ch) => ch?.destroy?.());
    charts = { v: null, w: null, dd: null };
  }

  function getPortfolioId() {
    const parts = new URL(window.location.href).pathname.split("/").filter(Boolean);
    return parts[1];
  }

  function getRange() {
    const url = new URL(window.location.href);
    return {
      start: url.searchParams.get("start") || "2022-02-15",
      end: url.searchParams.get("end") || "2022-08-01",
    };
  }

  // Retornos simples desde V(t)
  function calcReturns(V) {
    const r = [];
    for (let i = 1; i < V.length; i++) {
      const prev = V[i - 1];
      const cur = V[i];
      if (isFinite(prev) && isFinite(cur) && prev !== 0) r.push(cur / prev - 1);
    }
    return r;
  }

  function mean(arr) {
    return arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : 0;
  }

  function stdev(arr) {
    if (arr.length < 2) return 0;
    const m = mean(arr);
    const v = mean(arr.map((x) => (x - m) ** 2));
    return Math.sqrt(v);
  }

  // Drawdown: (V / maxHastaAhora) - 1
  function calcDrawdown(V) {
    let peak = -Infinity;
    return V.map((v) => {
      if (v > peak) peak = v;
      return peak > 0 ? v / peak - 1 : 0;
    });
  }

  function validatePayload(data) {
    if (!data || typeof data !== "object") throw new Error("Respuesta invalida: el JSON no es objeto.");
    if (!Array.isArray(data.rows)) throw new Error("Respuesta invalida: falta 'rows'.");
    if (!Array.isArray(data.assets)) throw new Error("Respuesta invalida: falta 'assets'.");
  }

  async function fetchTimeseries({ portfolioId, start, end, signal }) {
    const api = new URL(`/api/portfolios/${portfolioId}/timeseries/`, window.location.origin);
    api.searchParams.set("start", start);
    api.searchParams.set("end", end);

    const res = await fetch(api.toString(), {
      signal,
      credentials: "same-origin",
      headers: { Accept: "application/json" },
    });

    let body;
    try {
      body = await res.json();
    } catch (_) {
      // ignore, handled below
    }

    if (!res.ok) {
      const detail = body?.detail || body?.start || body?.error || res.statusText;
      throw new Error(`API error ${res.status}: ${detail}`);
    }

    validatePayload(body);
    return body;
  }

  function initChartDefaults() {
    Chart.defaults.font.family = "system-ui, -apple-system, Segoe UI, Roboto, Arial";
    Chart.defaults.plugins.legend.position = "bottom";
    Chart.defaults.plugins.tooltip.mode = "index";
    Chart.defaults.plugins.tooltip.intersect = false;
  }

  function buildValueChart({ labels, V }) {
    return new Chart(document.getElementById("vChart"), {
      type: "line",
      data: {
        labels,
        datasets: [{
          label: "Valor del portafolio V(t)",
          data: V,
          tension: 0.25,
          pointRadius: 0,
          borderWidth: 2,
          fill: true
        }]
      },
      options: {
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        scales: {
          y: { ticks: { callback: (val) => fmtUSD.format(val) } }
        }
      }
    });
  }

  function buildWeightsChart({ labels, rows, assets }) {
    const datasets = assets.map((a) => ({
      label: a,
      data: rows.map((r) => Number((r.weights && r.weights[a]) ?? 0)),
      pointRadius: 0,
      borderWidth: 1,
      tension: 0.25,
      fill: true,
      stack: "weights"
    }));

    return new Chart(document.getElementById("wChart"), {
      type: "line",
      data: { labels, datasets },
      options: {
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        plugins: {
          tooltip: {
            callbacks: {
              label: (ctx) => `${ctx.dataset.label}: ${fmtPct.format(ctx.parsed.y)}`
            }
          }
        },
        scales: {
          y: {
            stacked: true,
            min: 0,
            max: 1,
            ticks: { callback: (v) => fmtPct.format(v) }
          }
        }
      }
    });
  }

  function buildDrawdownChart({ labels, dd }) {
    return new Chart(document.getElementById("ddChart"), {
      type: "line",
      data: {
        labels,
        datasets: [{
          label: "Drawdown",
          data: dd,
          tension: 0.25,
          pointRadius: 0,
          borderWidth: 2,
          fill: true
        }]
      },
      options: {
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        plugins: {
          tooltip: {
            callbacks: {
              label: (ctx) => `Drawdown: ${fmtPct.format(ctx.parsed.y)}`
            }
          }
        },
        scales: {
          y: { ticks: { callback: (v) => fmtPct.format(v) } }
        }
      }
    });
  }

  function setKpis({ V }) {
    const v0 = V[0] ?? 0;
    const vT = V[V.length - 1] ?? 0;
    const ret = (v0 && vT) ? vT / v0 - 1 : 0;

    const r = calcReturns(V);
    const vol = stdev(r);

    const dd = calcDrawdown(V);
    const maxDD = dd.length ? Math.min(...dd) : 0;

    const ids = ["kpiValue", "kpiReturn", "kpiVol", "kpiDD"];
    const values = [
      isFinite(vT) ? fmtUSD.format(vT) : "--",
      isFinite(ret) ? fmtPct.format(ret) : "--",
      isFinite(vol) ? fmtPct.format(vol) : "--",
      isFinite(maxDD) ? fmtPct.format(maxDD) : "--",
    ];
    ids.forEach((id, idx) => {
      const node = document.getElementById(id);
      if (node) node.textContent = values[idx];
    });

    const ddMeta = document.getElementById("ddMeta");
    if (ddMeta) ddMeta.textContent = `Minimo: ${fmtPct.format(maxDD)}`;
    return dd;
  }

  async function load() {
    destroyCharts();
    setStatus("info", "Cargando datos...");

    if (abortCtl) abortCtl.abort();
    abortCtl = new AbortController();

    const portfolioId = getPortfolioId();
    const { start, end } = getRange();

    const badge = document.getElementById("rangeBadge");
    if (badge) badge.textContent = `Rango: ${start} a ${end}`;

    let data;
    try {
      data = await fetchTimeseries({ portfolioId, start, end, signal: abortCtl.signal });
    } catch (err) {
      console.error(err);
      setStatus("danger", err.message || "Fallo al obtener la serie.");
      return;
    }

    if (!data.rows.length) {
      setStatus("warning", "No hay datos en el rango seleccionado.");
      return;
    }

    const labels = data.rows.map((r) => r.date);
    const V = data.rows.map((r) => Number(r.V ?? 0));

    const vMeta = document.getElementById("vMeta");
    if (vMeta) vMeta.textContent = `${labels.length} puntos`;
    const wMeta = document.getElementById("wMeta");
    if (wMeta) wMeta.textContent = `${(data.assets || []).length} activos`;

    initChartDefaults();

    const dd = setKpis({ V });

    charts.v = buildValueChart({ labels, V });
    charts.w = buildWeightsChart({ labels, rows: data.rows, assets: data.assets });
    charts.dd = buildDrawdownChart({ labels, dd });

    setStatus(null, null);
  }

  document.addEventListener("DOMContentLoaded", () => {
    const reload = document.getElementById("btnReload");
    if (reload) {
      reload.addEventListener("click", () => {
        load().catch((err) => setStatus("danger", err.message));
      });
    }
    load().catch((err) => setStatus("danger", err.message));
  });
})();

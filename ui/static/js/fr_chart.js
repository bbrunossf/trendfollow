function setLoading(isLoading) {
  const overlay = document.getElementById("loadingOverlay");
  const btn = document.querySelector('.topbar-right button');
  if (!overlay || !btn) return;

  if (isLoading) {
    overlay.classList.remove("hidden");
    btn.disabled = true;
    btn.dataset.originalText = btn.dataset.originalText || btn.textContent;
    btn.textContent = "Loading...";
  } else {
    overlay.classList.add("hidden");
    btn.disabled = false;
    if (btn.dataset.originalText) {
      btn.textContent = btn.dataset.originalText;
    }
  }
}

async function runPipeline() {
  const dateInput = document.getElementById("referenceDate").value;

  let url = "/api/fr-price-series";
  if (dateInput) {
    url += `?reference_date=${dateInput}`;
  }

  setLoading(true);

  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error("Erro ao obter dados do backend");
    }

    const result = await response.json();

    // Gráfico 1 — Força Relativa
    Plotly.newPlot("chart", result.data, result.layout, { responsive: true });

    // Tabela de ranking
    if (typeof window.renderRankingTable === "function") {
      if (result && result.ranking) {
        window.renderRankingTable(result.ranking);
      } else {
        // Fallback: busca via endpoint dedicado se ranking não vier embutido
        if (typeof window.fetchAndRenderRankingTable === "function") {
          window.fetchAndRenderRankingTable(dateInput);
        }
      }
    }

    // Gráfico 3 — Dispersão: notifica scatterchart.js que o ranking está pronto
    if (result && result.ranking) {
      document.dispatchEvent(new CustomEvent("fr:rankingReady"));
    }
  } catch (error) {
    console.error(error);
    alert("Erro ao executar o pipeline.");
  } finally {
    setLoading(false);
  }
}

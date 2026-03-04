// /static/js/scatterchart.js
// Gráfico de dispersão Risco × Distância do Topo (52 semanas)
//
// Ciclo de vida:
//   1. Aguarda o evento customizado "fr:rankingReady" disparado por fr_chart.js
//      após o pipeline ser concluído.
//   2. Chama GET /api/scatterchart (leitura pura do cache — zero recomputação).
//   3. Exibe mensagem de carregamento enquanto aguarda a resposta.
//   4. Remove a mensagem e renderiza o payload Plotly no container #scatterchart,
//      ou exibe mensagem de erro — garantindo que a mensagem de carregamento
//      nunca persista após o desfecho da operação.

(function () {
  const CONTAINER_ID = "scatterchart";
  const ENDPOINT = "/api/scatterchart";

  // -----------------------------------------------------------------------
  // Helpers de estado do container
  // -----------------------------------------------------------------------

  function showLoading() {
    const container = document.getElementById(CONTAINER_ID);
    if (container) {
      container.innerHTML =
        '<p style="color: gray; padding: 10px;">Carregando gráfico de dispersão...</p>';
    }
  }

  function clearContainer() {
    const container = document.getElementById(CONTAINER_ID);
    if (container) {
      container.innerHTML = "";
    }
  }

  function showError(message) {
    const container = document.getElementById(CONTAINER_ID);
    if (container) {
      container.innerHTML =
        '<p style="color: red; padding: 10px;">Erro ao carregar gráfico de dispersão: ' +
        message +
        "</p>";
    }
  }

  // -----------------------------------------------------------------------
  // Renderização
  // -----------------------------------------------------------------------

  function renderScatterChart(payload) {
    // Limpa a mensagem de carregamento antes de qualquer decisão,
    // garantindo que ela nunca persista independente do caminho tomado.
    clearContainer();

    if (!payload || !payload.data || !payload.layout) {
      console.error("[scatterchart] Payload inválido:", payload);
      showError("Payload recebido do servidor está incompleto.");
      return;
    }

    const container = document.getElementById(CONTAINER_ID);
    if (!container) {
      console.warn(
        "[scatterchart] Container #" + CONTAINER_ID + " não encontrado no DOM.",
      );
      return;
    }

    Plotly.newPlot(CONTAINER_ID, payload.data, payload.layout, {
      responsive: true,
    });
  }

  // -----------------------------------------------------------------------
  // Fetch do endpoint
  // -----------------------------------------------------------------------

  async function fetchScatterChart() {
    showLoading();

    try {
      const response = await fetch(ENDPOINT);

      if (!response.ok) {
        const errorBody = await response.json().catch(() => null);
        const detail = errorBody?.detail || `HTTP ${response.status}`;
        throw new Error(detail);
      }

      const payload = await response.json();
      renderScatterChart(payload);
    } catch (error) {
      console.error(
        "[scatterchart] Erro ao carregar gráfico de dispersão:",
        error,
      );
      // clearContainer() já será chamado dentro de renderScatterChart
      // nos casos em que chegamos até lá. Para erros de rede/HTTP que
      // impedem renderScatterChart de ser chamado, limpamos aqui.
      clearContainer();
      showError(error.message);
    }
  }

  // -----------------------------------------------------------------------
  // Listener — aguarda o pipeline estar pronto
  // -----------------------------------------------------------------------

  document.addEventListener("DOMContentLoaded", function () {
    // O evento "fr:rankingReady" é disparado por fr_chart.js após
    // o pipeline ser concluído e o ranking estar disponível.
    document.addEventListener("fr:rankingReady", function () {
      console.log(
        "[scatterchart] Ranking pronto — carregando gráfico de dispersão.",
      );
      fetchScatterChart();
    });
  });
})();

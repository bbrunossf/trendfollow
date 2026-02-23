// /static/js/candlechart.js
// Renderização do gráfico de candlestick a partir do ticker selecionado na tabela

(function () {
    const containerId = "candlechart";

    /**
     * Renderiza o gráfico de candles usando Plotly
     */
    function renderCandleChart(payload) {
        if (!payload || !payload.data || !payload.layout) {
            console.error("Payload inválido para candlechart:", payload);
            return;
        }

        Plotly.newPlot(
            containerId,
            payload.data,
            payload.layout,
            { responsive: true }
        );
    }

    /**
     * Chama o endpoint /api/candlechart passando o ticker selecionado
     */
    async function fetchCandleChart(ticker) {
        if (!ticker) return;

        const url = `/api/candlechart?ticker=${encodeURIComponent(ticker)}`;

        try {
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`Erro HTTP ${response.status}`);
            }

            const payload = await response.json();
            renderCandleChart(payload);

        } catch (error) {
            console.error("Erro ao carregar candlechart:", error);
            alert("Erro ao gerar o gráfico de candles.");
        }
    }

    /**
     * Listener do evento customizado disparado pelo table.js
     * Espera receber { detail: { ticker: "PETR4" } }
     */
    document.addEventListener("DOMContentLoaded", () => {
        const tableContainer = document.getElementById("table");

        if (!tableContainer) {
            console.warn("Container da tabela não encontrado");
            return;
        }

        tableContainer.addEventListener("fr:rowSelected", (event) => {
            const rowData = event.detail || {};
            const ticker = rowData.ticker;

            if (!ticker) {
                console.warn("Ticker não encontrado no evento:", rowData);
                return;
            }

            console.log("Gerando candlechart para:", ticker);
            fetchCandleChart(ticker);
        });
    });

})();
async function runPipeline() {
    const dateInput = document.getElementById("referenceDate").value;

    let url = "/api/charts/fr-price-series";
    if (dateInput) {
        url += `?reference_date=${dateInput}`;
    }

    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error("Erro ao obter dados do backend");
        }

        const result = await response.json();

        Plotly.newPlot(
            "chart",
            result.data,
            result.layout,
            { responsive: true }
        );
		
		// após Plotly.newPlot(...)
		if (typeof window.renderRankingTable === "function") {
			if (result && result.ranking) {
				window.renderRankingTable(result.ranking);
			} else {
				// fallback: só chamar fetch se não houver ranking no response
				if (typeof window.fetchAndRenderRankingTable === "function") {
					window.fetchAndRenderRankingTable(dateInput);
				}
			}
		}

    } catch (error) {
        console.error(error);
        alert("Erro ao executar o pipeline.");
    }	
	
}

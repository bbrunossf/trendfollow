"""
Teste manual do pipeline para validação dos dados do gráfico de FR.

Objetivos:
- Rodar o pipeline completo
- Validar geração de FR e FR_rank
- Validar snapshots de preços (Adj Close)
- Construir o dataframe final usado no gráfico
- Garantir que não existe MultiIndex nessa etapa
"""

from datetime import date

from app.core.pipeline import run_pipeline
from app.data.preprocessing import (
    build_price_matrix_for_chart,
    add_percent_change_for_hover
)

# ---------------------------------------------------------
# Configurações do teste
# ---------------------------------------------------------
REFERENCE_DATE = "2026-01-13"
MIN_SCORE = 70


def main():
    print("▶ Rodando pipeline...")
    result = run_pipeline(reference_date=REFERENCE_DATE)

    assert "ranking" in result, "Pipeline não retornou ranking"
    assert result["ranking"], "Ranking vazio"

    ranking = result["ranking"]

    # -----------------------------------------------------
    # Validar FR e FR_rank
    # -----------------------------------------------------
    print("▶ Validando FR e FR_rank...")
    for item in ranking:
        assert "ticker" in item
        assert "FR" in item
        assert "FR_rank" in item

    selected_tickers = [
        item["ticker"]
        for item in ranking
        if item["FR_rank"] >= MIN_SCORE
    ]

    assert selected_tickers, "Nenhum ativo passou o filtro de FR_rank"

    print(f"✔ {len(selected_tickers)} ativos selecionados")

    # -----------------------------------------------------
    # Validar snapshots de preços
    # -----------------------------------------------------
    charts = result.get("charts", {})
    assert "price_snapshots" in charts, "price_snapshots ausente no pipeline"

    price_snapshots = charts["price_snapshots"]

    print("▶ Estrutura de price_snapshots:")
    print(price_snapshots.head())

    # -----------------------------------------------------
    # Construir dataframe base do gráfico
    # -----------------------------------------------------
    print("▶ Construindo matriz de preços para gráfico...")
    df_prices = build_price_matrix_for_chart(
        price_snapshots=price_snapshots,
        selected_tickers=selected_tickers,
        price_field="Adj Close"
    )

    assert not df_prices.empty, "DataFrame de preços vazio"
    assert df_prices.index.is_unique, "Índice de tickers não é único"

    print("✔ Matriz de preços OK")
    print(df_prices.head())

    # -----------------------------------------------------
    # Adicionar variação percentual (hover)
    # -----------------------------------------------------
    print("▶ Calculando variação percentual...")
    df_final = add_percent_change_for_hover(df_prices)
    
    print("status do df final:")
    print(df_final)
    print(df_final.columns)

    # -----------------------------------------------------
    # Validações finais
    # -----------------------------------------------------
    print("▶ Validações finais...")
    assert df_final.index.name == "Ticker"
    assert df_final.columns.is_unique
    assert not isinstance(df_final.columns, type(df_prices.columns)), \
        "Colunas ainda são MultiIndex"

    print("✔ DataFrame final pronto para Plotly")
    print(df_final.head())

    print("\n✅ TESTE CONCLUÍDO COM SUCESSO")


if __name__ == "__main__":
    main()

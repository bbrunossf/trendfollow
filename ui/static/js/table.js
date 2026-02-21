// /static/js/fr_table.js
// Renderizador de tabela usando Grid.js — somente tabela (sem gráfico)

// Fetch + render a partir do endpoint /api/ranking
async function fetchAndRenderRankingTable(referenceDate = '') {
    const url = `/api/ranking${referenceDate ? '?reference_date=' + encodeURIComponent(referenceDate) : ''}`;
    try {
        const resp = await fetch(url);
        if (!resp.ok) {
            console.error('Erro ao obter ranking:', resp.status, resp.statusText);
            renderEmptyTable('Erro ao obter dados.');
            return;
        }
        const data = await resp.json();
        renderRankingTable(data);
    } catch (err) {
        console.error('Erro ao buscar ranking:', err);
        renderEmptyTable('Erro ao obter dados2.');
    }
}

// Renderiza um array de objetos (records) usando Grid.js
function renderRankingTable(data) {
    const container = document.getElementById('table');
    if (!container) {
        console.warn('Container #table não encontrado no DOM.');
        return;
    }
    container.innerHTML = ''; // limpa

    if (!data || !Array.isArray(data) || data.length === 0) {
        renderEmptyTable('Nenhum dado disponível.');
        return;
    }

    // Normaliza chaves (ordem fixa: ticker primeiro se existir)
    const first = data[0];
    const keys = Object.keys(first);

    // opcional: força ordem útil — coloca 'ticker' ou 'Ticker' primeiro se existir
    const tickerKeyIndex = keys.findIndex(k => k.toLowerCase() === 'ticker');
    if (tickerKeyIndex > 0) {
        const [tk] = keys.splice(tickerKeyIndex, 1);
        keys.splice(0, 0, tk);
    }

    // Constrói os dados para Grid.js (array de arrays)
    const gridData = data.map(row => keys.map(k => formatCellValue(row[k])));

    // Colunas para Grid.js
    const columns = keys.map(k => ({
        id: k,
        name: k,
        // Você pode adicionar formatter aqui se quiser formatar números
    }));

    // Renderiza Grid.js
    const grid = new gridjs.Grid({
        columns: columns,
        data: gridData,
        sort: true,
        pagination: {
            enabled: true,
            limit: 20
        },
        resizable: true,
        fixedHeader: true,
        style: {
            // usa classes CSS do tema; cabeçalho customizado via CSS no index.html
        }
    });

    grid.render(container);

    // Adiciona highlight de linha via event delegation
    // (usa delegated click para encontrar .gridjs-tr)
    container.addEventListener('click', function (ev) {
        const tr = ev.target.closest('.gridjs-tr');
        if (!tr) return;
        // ignora cabeçalho
        if (tr.classList.contains('gridjs-head')) return;

        // remove seleção anterior
        const prev = container.querySelectorAll('.gridjs-tr.selected');
        prev.forEach(r => r.classList.remove('selected'));

        // aplica seleção
        tr.classList.add('selected');

        // opcional: expõe evento customizado com os dados da linha
        const cells = Array.from(tr.querySelectorAll('.gridjs-td')).map(td => td.textContent.trim());
        const rowObj = {};
        keys.forEach((k, idx) => rowObj[k] = cells[idx]);
        // dispara evento custom no container (ou use console.log)
        const evt = new CustomEvent('fr:rowSelected', { detail: rowObj });
        container.dispatchEvent(evt);
    }, false);
}

// formata valor de célula de forma simples
function formatCellValue(v) {
    if (v === null || typeof v === 'undefined') return '';
    // se for número, formata com 2 decimais (mas mantém tipo string para exibição)
    if (typeof v === 'number' && isFinite(v)) {
        return Number.isInteger(v) ? v.toString() : v.toFixed(2);
    }
    // se for objeto/array, stringify de forma simples
    if (typeof v === 'object') return JSON.stringify(v);
    return String(v);
}

function renderEmptyTable(message) {
    const container = document.getElementById('table');
    if (!container) return;
    container.innerHTML = `<p>${message}</p>`;
}

// Expõe funções globalmente para que fr_chart.js possa chamar quando desejar
window.fetchAndRenderRankingTable = fetchAndRenderRankingTable;
window.renderRankingTable = renderRankingTable;

// Auto-load ao carregar a página (sem referência de data)
// document.addEventListener('DOMContentLoaded', function () {
    // Carrega tabela padrão sem reference_date (você pode remover se preferir carregar somente via chamada explícita)
    // fetchAndRenderRankingTable();
// });
document.addEventListener('DOMContentLoaded', function () {
    const rawRecordsElement = document.getElementById('review-records-data');
    const records = rawRecordsElement ? JSON.parse(rawRecordsElement.textContent) : [];
    const table = document.getElementById('reviewTable');

    function getRecord(index) {
        index = parseInt(index, 10);
        if (Number.isNaN(index) || index < 0 || index >= records.length) return null;
        return records[index];
    }

    function setText(id, value) {
        const el = document.getElementById(id);
        if (!el) return;
        el.textContent = (value === null || value === undefined || value === '') ? '-' : String(value);
    }

    function openModalForIndex(index) {
        const rec = getRecord(index);
        if (!rec) return;

        setText('rv-logradouro-original', rec.logradouro || '');
        setText('rv-logradouro-normalizado', rec.logradouro_normalizado || '');
        setText('rv-logradouro-limpo', rec.logradouro_limpo || '');
        setText('rv-logradouro-canonico', rec.logradouro_canonico || '');
        setText('rv-correcao-manual', rec.correcao_manual_nome || (rec.correcao_manual_aplicada ? 'SIM' : '-'));
        setText('rv-confianca', rec.confianca_matching || '-');
        setText('rv-similaridade', rec.similaridade || '-');
        setText('rv-frequencia', rec.frequencia_grupo || 0);
        setText('rv-latitude', rec.latitude || '-');
        setText('rv-longitude', rec.longitude || '-');
        setText('rv-status-revisao', rec.status_revisao || '-');

        const modalEl = document.getElementById('reviewModal');
        if (!modalEl) return;
        const modal = new bootstrap.Modal(modalEl);
        modal.show();
    }

    if (table) {
        table.addEventListener('click', function (ev) {
            const btn = ev.target.closest('.btn-review');
            if (!btn) return;
            const idx = btn.getAttribute('data-index');
            openModalForIndex(idx);
        });
    }

});

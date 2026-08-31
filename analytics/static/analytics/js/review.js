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

        // text-only fields
        setText('rv-logradouro-original', rec.logradouro || '');
        setText('rv-logradouro-normalizado', rec.logradouro_normalizado || '');
        setText('rv-logradouro-limpo', rec.logradouro_limpo || '');
        document.getElementById('rv-logradouro-canonico').value = rec.logradouro_canonico || '';
        setText('rv-correcao-manual', rec.correcao_manual_nome || (rec.correcao_manual_aplicada ? 'SIM' : '-'));
        setText('rv-confianca', rec.confianca_matching || '-');
        setText('rv-similaridade', rec.similaridade || '-');
        setText('rv-frequencia', rec.frequencia_grupo || 0);
        setText('rv-latitude', rec.latitude || '-');
        setText('rv-longitude', rec.longitude || '-');
        document.getElementById('rv-status-revisao').value = rec.status_revisao || 'PENDENTE';
        document.getElementById('rv-autor').value = rec.autor || '';
        document.getElementById('rv-note').value = rec.note || '';

        // store current index on modal for save
        const modalEl = document.getElementById('reviewModal');
        modalEl.setAttribute('data-current-index', String(index));

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

    // CSRF helper (reads cookie)
    function getCookie(name) {
        const v = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
        return v ? v.pop() : '';
    }

    // Save handler
    const saveBtn = document.getElementById('rv-save-btn');
    if (saveBtn) {
        saveBtn.addEventListener('click', function () {
            const modalEl = document.getElementById('reviewModal');
            const idx = parseInt(modalEl.getAttribute('data-current-index'), 10);
            const rec = getRecord(idx);
            if (!rec) return;

            const payload = {
                logradouro_original: rec.logradouro || '',
                logradouro_limpo: rec.logradouro_limpo || '',
                logradouro_canonico: document.getElementById('rv-logradouro-canonico').value || '',
                status: document.getElementById('rv-status-revisao').value || 'PENDENTE',
                autor: document.getElementById('rv-autor').value || '',
                note: document.getElementById('rv-note').value || '',
            };

            fetch('/review/save/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                body: JSON.stringify(payload),
            }).then(r => r.json()).then(data => {
                if (data && data.success) {
                    const updated = data.data || {};
                    // update local record and table
                    records[idx].logradouro_canonico = updated.logradouro_canonico || records[idx].logradouro_canonico;
                    records[idx].status_revisao = updated.status || records[idx].status_revisao;
                    records[idx].autor = updated.autor || records[idx].autor;
                    // close modal
                    const modal = bootstrap.Modal.getInstance(document.getElementById('reviewModal'));
                    if (modal) modal.hide();
                    // update table row visually
                    const row = document.querySelector(`#reviewTable tbody tr[data-index="${idx}"]`);
                    if (row) {
                        const canonicoCell = row.querySelector('.cell-canonico');
                        const statusCell = row.querySelector('.cell-status');
                        if (canonicoCell) canonicoCell.textContent = records[idx].logradouro_canonico || '-';
                        if (statusCell) statusCell.textContent = records[idx].status_revisao || '-';
                    }
                    // optionally show a quick alert
                    alert('Correção salva com sucesso.');
                } else {
                    alert('Erro ao salvar: ' + (data && data.error ? data.error : 'Resposta inválida'));
                }
            }).catch(err => {
                alert('Erro na requisição: ' + String(err));
            });
        });
    }

});

/**
 * Dataset Edit Module
 * 
 * Handles the modal-based editing of dataset records.
 * Responsible for:
 * - Opening/closing the edit modal
 * - Populating form fields with record data
 * - Displaying audit history
 * - Collecting and validating changes
 * - Sending POST requests to the backend
 * - Updating rows after successful save
 * - Preventing duplicate submissions
 */

(function() {
    'use strict';

    // DOM Elements
    const editModal = document.getElementById('editRecordModal');
    const editIdRegistro = document.getElementById('edit-id-registro');
    const editLogradouroOriginal = document.getElementById('edit-logradouro-original');
    const editNumeroLogradouro = document.getElementById('edit-numero-logradouro');
    const editLogradouroSugerido = document.getElementById('edit-logradouro-sugerido');
    const editLogradouroCanonico = document.getElementById('edit-logradouro-canonico');
    const editAuditHistory = document.getElementById('edit-audit-history');
    const editNote = document.getElementById('edit-note');
    const btnSaveRecord = document.getElementById('btn-save-record');
    const editRecordButtons = document.querySelectorAll('.btn-edit-record');

    // State
    let isSubmitting = false;
    let recordsData = [];

    /**
     * Initialize the module
     */
    function init() {
        loadRecordsData();
        attachEventListeners();
    }

    /**
     * Load records from the json_script
     */
    function loadRecordsData() {
        const dataElement = document.getElementById('dataset-records-data');
        if (dataElement) {
            try {
                recordsData = JSON.parse(dataElement.textContent);
            } catch (e) {
                console.error('Failed to parse records data:', e);
            }
        }
    }

    /**
     * Attach event listeners to edit buttons
     */
    function attachEventListeners() {
        editRecordButtons.forEach(button => {
            button.addEventListener('click', handleEditClick);
        });

        if (btnSaveRecord) {
            btnSaveRecord.addEventListener('click', handleSaveClick);
        }

        if (editModal) {
            editModal.addEventListener('hidden.bs.modal', resetForm);
        }
    }

    /**
     * Handle edit button click
     */
    function handleEditClick(e) {
        e.preventDefault();
        const idRegistro = e.currentTarget.getAttribute('data-id-registro');
        const record = findRecord(idRegistro);

        if (record) {
            populateForm(record);
            openModal();
        } else {
            showError('Registro não encontrado');
        }
    }

    /**
     * Find a record by id_registro
     */
    function findRecord(idRegistro) {
        return recordsData.find(r => r.id_registro === idRegistro);
    }

    /**
     * Populate the form with record data
     */
    function populateForm(record) {
        editIdRegistro.value = record.id_registro;
        editLogradouroOriginal.textContent = record.logradouro || '-';
        editNumeroLogradouro.value = record.numero_logradouro !== null ? record.numero_logradouro : '';
        editLogradouroSugerido.textContent = record.logradouro_sugerido || '-';
        editLogradouroCanonico.value = record.logradouro_canonico || '';
        editNote.value = '';

        populateAuditHistory(record.audits);
    }

    /**
     * Populate the audit history section
     */
    function populateAuditHistory(audits) {
        if (!audits || audits.length === 0) {
            editAuditHistory.innerHTML = '<span class="text-muted">Nenhuma alteração registrada.</span>';
            return;
        }

        let historyHtml = '<div class="timeline">';

        audits.forEach(audit => {
            const auditDate = audit.created_at || 'Data indisponível';
            const auditUser = audit.usuario || 'Usuário indisponível';
            const fieldName = formatFieldName(audit.field_name);
            const note = audit.note ? `<div class="small text-muted">Observação: ${escapeHtml(audit.note)}</div>` : '';

            historyHtml += `
                <div class="mb-3 pb-3 border-bottom">
                    <div class="small fw-bold text-primary">${fieldName}</div>
                    <div class="small">
                        <span class="text-muted">${auditDate}</span>
                        <span class="text-muted ms-2">por ${escapeHtml(auditUser)}</span>
                    </div>
                    <div class="small mt-1">
                        <span class="text-muted">De: </span>
                        <code>${escapeHtml(audit.previous_value || '(vazio)')}</code>
                    </div>
                    <div class="small">
                        <span class="text-muted">Para: </span>
                        <code>${escapeHtml(audit.new_value || '(vazio)')}</code>
                    </div>
                    ${note}
                </div>
            `;
        });

        historyHtml += '</div>';
        editAuditHistory.innerHTML = historyHtml;
    }

    /**
     * Format field name for display
     */
    function formatFieldName(fieldName) {
        const fieldLabels = {
            'numero_logradouro': 'Número do logradouro',
            'logradouro_canonico': 'Logradouro canônico',
        };
        return fieldLabels[fieldName] || fieldName;
    }

    /**
     * Escape HTML to prevent XSS
     */
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Open the modal
     */
    function openModal() {
        const bsModal = new bootstrap.Modal(editModal);
        bsModal.show();
    }

    /**
     * Reset the form
     */
    function resetForm() {
        editIdRegistro.value = '';
        editLogradouroOriginal.textContent = '-';
        editNumeroLogradouro.value = '';
        editLogradouroSugerido.textContent = '-';
        editLogradouroCanonico.value = '';
        editNote.value = '';
        editAuditHistory.innerHTML = '<span class="text-muted">Nenhuma alteração registrada.</span>';
        isSubmitting = false;
    }

    /**
     * Handle save button click
     */
    function handleSaveClick(e) {
        e.preventDefault();

        if (isSubmitting) {
            return;
        }

        // Validate form
        const validation = validateForm();
        if (!validation.valid) {
            showError(validation.message);
            return;
        }

        // Collect changes
        const changes = collectChanges();
        if (Object.keys(changes).length === 0) {
            showWarning('Nenhuma alteração foi feita');
            return;
        }

        // Send request
        isSubmitting = true;
        btnSaveRecord.disabled = true;

        sendUpdateRequest(changes)
            .then(response => {
                showSuccess('Registro atualizado com sucesso!');
                updateRowDisplay(validation.idRegistro);
                closeModal();
                setTimeout(() => {
                    location.reload();
                }, 500);
            })
            .catch(error => {
                showError(error);
            })
            .finally(() => {
                isSubmitting = false;
                btnSaveRecord.disabled = false;
            });
    }

    /**
     * Validate the form
     */
    function validateForm() {
        const idRegistro = editIdRegistro.value.trim();
        const numeroLogradouro = editNumeroLogradouro.value.trim();
        const logradouroCanonico = editLogradouroCanonico.value.trim();

        if (!idRegistro) {
            return { valid: false, message: 'ID do registro não encontrado' };
        }

        // Validate numero_logradouro if provided
        if (numeroLogradouro !== '') {
            if (isNaN(numeroLogradouro)) {
                return { valid: false, message: 'Número deve ser um valor numérico' };
            }
        }

        return { valid: true, idRegistro };
    }

    /**
     * Collect changes from the form
     */
    function collectChanges() {
        const changes = {};
        const record = findRecord(editIdRegistro.value);

        if (!record) {
            return changes;
        }

        const numeroLogradouro = editNumeroLogradouro.value.trim();
        const logradouroCanonico = editLogradouroCanonico.value.trim();

        // Check numero_logradouro
        const originalNumero = record.numero_logradouro !== null ? String(record.numero_logradouro) : '';
        if (numeroLogradouro !== originalNumero) {
            changes.numero_logradouro = numeroLogradouro === '' ? null : parseFloat(numeroLogradouro);
        }

        // Check logradouro_canonico
        const originalCanonico = record.logradouro_canonico || '';
        if (logradouroCanonico !== originalCanonico) {
            changes.logradouro_canonico = logradouroCanonico;
        }

        return changes;
    }

    /**
     * Send update request to the backend
     */
    function sendUpdateRequest(updates) {
        return new Promise((resolve, reject) => {
            const idRegistro = editIdRegistro.value;
            const note = editNote.value.trim();
            const csrfToken = getCsrfToken();

            const payload = {
                id_registro: idRegistro,
                updates: updates,
                note: note,
            };

            fetch(getUpdateUrl(), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
                body: JSON.stringify(payload),
            })
                .then(response => {
                    if (!response.ok) {
                        return response.json().then(data => {
                            throw new Error(data.error || 'Erro ao salvar registro');
                        });
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.success) {
                        resolve(data);
                    } else {
                        reject(data.error || 'Erro desconhecido');
                    }
                })
                .catch(error => {
                    reject(error.message || 'Erro de conexão');
                });
        });
    }

    /**
     * Get CSRF token from the page
     */
    function getCsrfToken() {
        const name = 'csrftoken';
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith(name + '='))
            ?.split('=')[1];

        return cookieValue || '';
    }

    /**
     * Get the update URL from the current page
     */
    function getUpdateUrl() {
        // Extract dataset_id from the current URL
        const match = window.location.pathname.match(/\/datasets\/(\d+)\//);
        if (match) {
            return `/datasets/${match[1]}/editar/`;
        }
        return '/datasets/editar/';
    }

    /**
     * Update the row display after successful save
     */
    function updateRowDisplay(idRegistro) {
        const record = findRecord(idRegistro);
        if (!record) {
            return;
        }

        const row = document.querySelector(`tr[data-id-registro="${idRegistro}"]`);
        if (!row) {
            return;
        }

        // Update visible columns
        const cells = row.querySelectorAll('td');
        if (cells.length >= 5) {
            cells[1].textContent = record.numero_logradouro !== null ? record.numero_logradouro : '-';
            cells[3].textContent = record.logradouro_canonico || '-';
        }
    }

    /**
     * Close the modal
     */
    function closeModal() {
        const bsModal = bootstrap.Modal.getInstance(editModal);
        if (bsModal) {
            bsModal.hide();
        }
    }

    /**
     * Show success message
     */
    function showSuccess(message) {
        showAlert(message, 'success');
    }

    /**
     * Show error message
     */
    function showError(message) {
        showAlert(message, 'danger');
    }

    /**
     * Show warning message
     */
    function showWarning(message) {
        showAlert(message, 'warning');
    }

    /**
     * Show alert using Bootstrap toast or simple alert
     */
    function showAlert(message, type) {
        // Try using Bootstrap toast if available
        const alertId = `alert-${Date.now()}`;
        const alertHtml = `
            <div id="${alertId}" class="alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x" role="alert" style="z-index: 9999;">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Fechar"></button>
            </div>
        `;

        const alertContainer = document.createElement('div');
        alertContainer.innerHTML = alertHtml;
        document.body.appendChild(alertContainer);

        setTimeout(() => {
            const alert = document.getElementById(alertId);
            if (alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
                setTimeout(() => alertContainer.remove(), 150);
            }
        }, 4000);
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();

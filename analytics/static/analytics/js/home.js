document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('uploadForm');
    const submitButton = document.getElementById('submitButton');
    const loader = document.getElementById('pageLoader');
    const fileInput = document.querySelector('input[type="file"]');
    const fileHint = document.getElementById('fileNameHint');
    const selects = Array.from(document.querySelectorAll('select[name="tipo_via"], select[name="tipo_sinistro"]'));
    const storageKey = 'infosigaAnalyticsFilters';

    function loadSavedFilters() {
        try {
            const saved = JSON.parse(localStorage.getItem(storageKey) || '{}');
            selects.forEach((select) => {
                if (saved[select.name]) {
                    select.value = saved[select.name];
                }
            });
        } catch (error) {
            console.warn('Não foi possível restaurar os filtros salvos.', error);
        }
    }

    function saveFilters() {
        const payload = {};
        selects.forEach((select) => {
            if (select.value) {
                payload[select.name] = select.value;
            }
        });
        localStorage.setItem(storageKey, JSON.stringify(payload));
    }

    selects.forEach((select) => {
        select.addEventListener('change', saveFilters);
    });

    if (fileInput && fileHint) {
        fileInput.addEventListener('change', function () {
            if (fileInput.files && fileInput.files.length > 0) {
                fileHint.textContent = fileInput.files[0].name;
            } else {
                fileHint.textContent = 'Nenhum ficheiro selecionado';
            }
        });
    }

    if (form) {
        form.addEventListener('submit', function () {
            saveFilters();
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Carregando...';
            }
            if (loader) {
                loader.classList.add('active');
            }
        });
    }

    window.addEventListener('load', function () {
        loadSavedFilters();
        if (loader) {
            loader.classList.remove('active');
        }
    });
});

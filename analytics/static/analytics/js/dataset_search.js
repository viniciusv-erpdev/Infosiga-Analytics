(function () {
    'use strict';

    const searchInput = document.getElementById('dataset-search');
    const searchButton = document.getElementById('dataset-search-button');
    const suggestionsContainer = document.getElementById(
        'dataset-search-suggestions'
    );

    if (!searchInput || !suggestionsContainer) {
        return;
    }

    let debounceTimer = null;
    let currentController = null;

    function getDatasetId() {
        const match = window.location.pathname.match(
            /\/datasets\/(\d+)\//
        );

        return match ? match[1] : null;
    }

    function searchUrl(query) {
        const url = new URL(
            window.location.href
        );

        url.searchParams.set('q', query);
        url.searchParams.delete('page');

        return url.toString();
    }

    function suggestionsUrl(query) {
        const datasetId = getDatasetId();

        if (!datasetId) {
            return null;
        }

        return `/datasets/${datasetId}/sugestoes/?q=${encodeURIComponent(query)}`;
    }

    function clearSuggestions() {
        suggestionsContainer.innerHTML = '';
        suggestionsContainer.classList.add('d-none');
    }

    function renderSuggestions(suggestions) {
        suggestionsContainer.innerHTML = '';

        if (!suggestions || suggestions.length === 0) {
            suggestionsContainer.classList.add('d-none');
            return;
        }

        suggestions.forEach(suggestion => {
            const button = document.createElement('button');

            button.type = 'button';
            button.className =
                'list-group-item list-group-item-action';

            const value = suggestion.value;

            button.innerHTML = `
                <div class="d-flex justify-content-between align-items-center">
                    <span>${escapeHtml(value)}</span>
                </div>
            `;

            button.addEventListener(
                'click',
                () => selectSuggestion(value)
            );

            suggestionsContainer.appendChild(button);
        });

        suggestionsContainer.classList.remove('d-none');
    }

    async function loadSuggestions(query) {
        const url = suggestionsUrl(query);

        if (!url) {
            return;
        }

        if (currentController) {
            currentController.abort();
        }

        currentController = new AbortController();

        try {
            const response = await fetch(
                url,
                {
                    method: 'GET',
                    headers: {
                        'Accept': 'application/json',
                    },
                    signal: currentController.signal,
                }
            );

            if (!response.ok) {
                throw new Error(
                    'Não foi possível carregar sugestões.'
                );
            }

            const data = await response.json();

            renderSuggestions(
                data.suggestions || []
            );

        } catch (error) {
            if (error.name === 'AbortError') {
                return;
            }

            console.error(
                'Erro ao carregar sugestões:',
                error
            );

            clearSuggestions();
        }
    }

    function handleInput() {
        const query = searchInput.value.trim();

        clearTimeout(debounceTimer);

        if (query.length < 3) {
            clearSuggestions();
            return;
        }

        debounceTimer = setTimeout(
            () => loadSuggestions(query),
            300
        );
    }

    function executeSearch() {
        const query = searchInput.value.trim();

        if (!query) {
            return;
        }

        window.location.href = searchUrl(query);
    }

    function selectSuggestion(value) {
        searchInput.value = value;
        clearSuggestions();
        executeSearch();
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    searchInput.addEventListener(
        'input',
        handleInput
    );

    searchInput.addEventListener(
        'keydown',
        event => {
            if (event.key === 'Enter') {
                event.preventDefault();
                clearSuggestions();
                executeSearch();
            }

            if (event.key === 'Escape') {
                clearSuggestions();
            }
        }
    );

    searchButton?.addEventListener(
        'click',
        executeSearch
    );

    document.addEventListener(
        'click',
        event => {
            if (
                !searchInput.contains(event.target) &&
                !suggestionsContainer.contains(event.target)
            ) {
                clearSuggestions();
            }
        }
    );

})();
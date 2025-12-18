// static/js/search.js
class PlayerSearch {
    constructor() {
        this.searchInput = document.getElementById('player-search');
        this.searchForm = document.getElementById('player-search-form');
        this.searchResults = document.getElementById('search-results');
        this.searchTimeout = null;
        this.currentSearchResults = [];

        this.init();
    }

    init() {
        // Debounced search on input
        this.searchInput.addEventListener('input', (e) => {
            clearTimeout(this.searchTimeout);
            const query = e.target.value.trim();

            if (query.length < 2) {
                this.hideResults();
                return;
            }

            this.searchTimeout = setTimeout(() => {
                this.performSearch(query);
            }, 300);
        });

        // Show results when focused with existing query
        this.searchInput.addEventListener('focus', () => {
            const query = this.searchInput.value.trim();
            if (query.length >= 2 && this.currentSearchResults.length > 0) {
                this.showResults();
            }
        });

        // Hide results when clicking outside
        document.addEventListener('click', (e) => {
            if (!this.searchForm.contains(e.target)) {
                this.hideResults();
            }
        });

        // Handle form submission
        this.searchForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const query = this.searchInput.value.trim();
            if (query) {
                this.performSearch(query);
            }
        });

        // Keyboard shortcuts
        this.setupKeyboardShortcuts();
    }

    async performSearch(query) {
        try {
            this.showLoading();

            const response = await fetch(`/api/search-players?q=${encodeURIComponent(query)}`);
            const players = await response.json();

            this.currentSearchResults = players;
            this.displaySearchResults(players);

        } catch (error) {
            console.error('Search error:', error);
            this.showError();
        }
    }

    displaySearchResults(players) {
        if (players.length === 0) {
            this.searchResults.innerHTML = '<div class="no-results">No players found</div>';
            this.showResults();
            return;
        }

        const resultsHtml = players.map(player => `
            <div class="search-result-item" data-player-id="${player.id}">
                <div class="player-info">
                    <div class="player-name">${player.first_name} ${player.last_name}</div>
                    <div class="player-details">
                        • Rating: ${player.current_rating || 'N/A'}
                    </div>
                </div>
            </div>
        `).join('');

        this.searchResults.innerHTML = resultsHtml;
        this.addResultClickHandlers(players);
        this.showResults();
    }

    addResultClickHandlers(players) {
        document.querySelectorAll('.search-result-item').forEach(item => {
            item.addEventListener('click', () => {
                const playerId = item.getAttribute('data-player-id');
                const player = players.find(p => p.id == playerId);
                if (player) {
                    window.location.href = `/player/${playerId}`;
                }
            });
        });
    }

    showLoading() {
        this.searchResults.innerHTML = '<div class="search-loading">Searching players...</div>';
        this.showResults();
    }

    showError() {
        this.searchResults.innerHTML = '<div class="no-results">Error loading search results</div>';
        this.showResults();
    }

    showResults() {
        this.searchResults.style.display = 'block';
    }

    hideResults() {
        this.searchResults.style.display = 'none';
    }

    getInitials(firstName, lastName) {
        return (firstName.charAt(0) + lastName.charAt(0)).toUpperCase();
    }

    setupKeyboardShortcuts() {
        // Ctrl/Cmd + K to focus search
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                this.searchInput.focus();
                this.searchInput.select();
            }

            // ESC to close search results
            if (e.key === 'Escape' && this.searchResults.style.display === 'block') {
                this.hideResults();
                this.searchInput.blur();
            }
        });

        // Clear search when pressing escape while focused
        this.searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.searchInput.value === '') {
                this.searchInput.blur();
                this.hideResults();
            }
        });
    }
}

// Initialize search when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('player-search-form')) {
        new PlayerSearch();
    }
});
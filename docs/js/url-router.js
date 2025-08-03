// URL Router for handling navigation between dashboard and details view
class URLRouter {
    constructor() {
        this.currentView = 'dashboard';
        this.currentParams = {};
        this.setupHistoryHandling();
        this.parseCurrentURL();
    }

    parseCurrentURL() {
        const urlParams = new URLSearchParams(window.location.search);
        const view = urlParams.get('view') || 'dashboard';
        const category = urlParams.get('category');
        const subcategory = urlParams.get('subcategory');

        this.currentView = view;
        this.currentParams = {
            category: category,
            subcategory: subcategory
        };
    }

    getCurrentView() {
        return this.currentView;
    }

    getParams() {
        return { ...this.currentParams };
    }

    navigateTo(view, params = {}) {
        this.currentView = view;
        this.currentParams = { ...params };

        // Update URL without page reload
        const url = new URL(window.location);
        url.searchParams.set('view', view);

        if (params.category) {
            url.searchParams.set('category', params.category);
        } else {
            url.searchParams.delete('category');
        }

        if (params.subcategory) {
            url.searchParams.set('subcategory', params.subcategory);
        } else {
            url.searchParams.delete('subcategory');
        }

        window.history.pushState({ view, params }, '', url);

        // Trigger view change
        this.onViewChange(view, params);
    }

    setupHistoryHandling() {
        window.addEventListener('popstate', (event) => {
            this.parseCurrentURL();
            this.onViewChange(this.currentView, this.currentParams);
        });
    }

    onViewChange(view, params) {
        // This will be overridden by the dashboard
    }
}
// Initialize dashboard when page loads
let dashboard;
document.addEventListener('DOMContentLoaded', () => {
    dashboard = new BenchmarkDashboard();

    // Set up back button handler
    document.getElementById('back-to-dashboard').addEventListener('click', (e) => {
        e.preventDefault();
        dashboard.navigateBackToDashboard();
    });
});
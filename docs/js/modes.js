// Theme toggle functionality
const themeToggle = document.getElementById('theme-toggle');
const body = document.body;

// Check for saved theme preference or default to light mode
const currentTheme = localStorage.getItem('theme') || 'light';
console.log('Initial theme:', currentTheme);
body.setAttribute('data-theme', currentTheme);

themeToggle.addEventListener('click', () => {
    const currentTheme = body.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    console.log('Switching from', currentTheme, 'to', newTheme);
    body.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    
    // Force a style recalculation
    body.style.display = 'none';
    body.offsetHeight; // Trigger reflow
    body.style.display = '';
});
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
    
    // Add switching animation class
    themeToggle.classList.add('switching');
    
    // Apply the new theme after a brief delay for the button animation
    setTimeout(() => {
        body.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
    }, 200);
    
    // Remove animation class after animation completes
    setTimeout(() => {
        themeToggle.classList.remove('switching');
    }, 600);
});
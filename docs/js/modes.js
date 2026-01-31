const themeToggle = document.getElementById('theme-toggle');
const body = document.body;

const currentTheme = localStorage.getItem('theme') || 'light';
console.log('Initial theme:', currentTheme);
body.setAttribute('data-theme', currentTheme);

themeToggle.addEventListener('click', () => {
    const currentTheme = body.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    console.log('Switching from', currentTheme, 'to', newTheme);
    
    themeToggle.classList.add('switching');
    
    body.style.opacity = '0.95';
    
    setTimeout(() => {
        body.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
    }, 150);
    
    setTimeout(() => {
        body.style.opacity = '1';
        themeToggle.classList.remove('switching');
    }, 400);
});
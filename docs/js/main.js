// Initialize dashboard when page loads
let dashboard;
document.addEventListener('DOMContentLoaded', () => {
    dashboard = new BenchmarkDashboard();

    // Set up back button handler
    document.getElementById('back-to-dashboard').addEventListener('click', (e) => {
        e.preventDefault();
        dashboard.navigateBackToDashboard();
    });

    // Initialize API code tabs
    initializeApiTabs();

    // Initialize copy functionality
    initializeCopyButtons();

    // Initialize scroll navbar
    initializeScrollNavbar();
});

// API Code Tabs functionality
function initializeApiTabs() {
    // Initialize usage example tabs
    initializeTabGroup('.code-tabs');

    // Initialize data structure tabs
    initializeTabGroup('.structure-tabs');
}

function initializeTabGroup(containerSelector) {
    const container = document.querySelector(containerSelector);
    if (!container) return;

    const tabButtons = container.querySelectorAll('.tab-button');
    const tabPanes = container.querySelectorAll('.tab-pane');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetTab = button.getAttribute('data-tab');

            // Remove active class from buttons and panes within this container only
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabPanes.forEach(pane => pane.classList.remove('active'));

            // Add active class to clicked button and corresponding pane
            button.classList.add('active');
            const targetPane = container.querySelector(`#${targetTab}-tab`);
            if (targetPane) {
                targetPane.classList.add('active');
            }
        });
    });
}

// Copy to clipboard functionality
function initializeCopyButtons() {
    const copyButtons = document.querySelectorAll('.copy-button');

    copyButtons.forEach(button => {
        button.addEventListener('click', async (e) => {
            e.preventDefault();
            e.stopPropagation();

            const textToCopy = button.getAttribute('data-copy');

            try {
                await navigator.clipboard.writeText(textToCopy);
                showCopySuccess(button);
            } catch (err) {
                // Fallback for older browsers
                fallbackCopyTextToClipboard(textToCopy, button);
            }
        });
    });
}

function showCopySuccess(button) {
    const originalClass = button.className;
    button.classList.add('copied');

    // Create and show tooltip
    const tooltip = document.createElement('div');
    tooltip.className = 'copy-tooltip';
    tooltip.textContent = 'Copied!';

    // Get button position relative to the document
    const rect = button.getBoundingClientRect();
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;

    tooltip.style.cssText = `
        position: absolute;
        top: ${rect.top + scrollTop - 35}px;
        left: ${rect.left + scrollLeft + button.offsetWidth / 2}px;
        background: #d4af37;
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
        white-space: nowrap;
        z-index: 1000;
        pointer-events: none;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
    `;

    document.body.appendChild(tooltip);

    // Trigger show animation after a brief delay to ensure element is in DOM
    requestAnimationFrame(() => {
        tooltip.classList.add('show');
    });

    // Start hide animation after 1.5 seconds
    setTimeout(() => {
        tooltip.classList.remove('show');
        tooltip.classList.add('hide');

        // Remove button copied state and tooltip after hide animation completes
        setTimeout(() => {
            button.className = originalClass;
            if (tooltip.parentNode) {
                tooltip.parentNode.removeChild(tooltip);
            }
        }, 300); // Match the CSS transition duration
    }, 1500);
}

function fallbackCopyTextToClipboard(text, button) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();

    try {
        document.execCommand('copy');
        showCopySuccess(button);
    } catch (err) {
        console.error('Fallback: Oops, unable to copy', err);
    }

    document.body.removeChild(textArea);
}

// Scroll navbar
function initializeScrollNavbar() {
    const navbar = document.getElementById('scroll-navbar');
    const socialLinks = document.querySelector('.social-links');
    
    if (!navbar || !socialLinks) return;

    let isNavbarVisible = false;
    let ticking = false;

    function updateStickyOffset(navbarVisible) {
        // Update CSS custom property for sticky header offset
        let offset = '0px';
        if (navbarVisible) {
            // Get the actual navbar height
            const navbarHeight = navbar.offsetHeight;
            offset = `${navbarHeight}px`;
        }
        document.documentElement.style.setProperty('--sticky-top-offset', offset);
    }

    function updateNavbar() {
        const socialLinksRect = socialLinks.getBoundingClientRect();
        const socialLinksBottom = socialLinksRect.bottom;
        
        // Show navbar when scrolling over the main buttons
        const shouldShowNavbar = socialLinksBottom < 0;

        if (shouldShowNavbar && !isNavbarVisible) {
            navbar.classList.add('visible');
            isNavbarVisible = true;
            updateStickyOffset(true);
        } else if (!shouldShowNavbar && isNavbarVisible) {
            navbar.classList.remove('visible');
            isNavbarVisible = false;
            updateStickyOffset(false);
        }

        ticking = false;
    }

    function requestTick() {
        if (!ticking) {
            requestAnimationFrame(updateNavbar);
            ticking = true;
        }
    }

    // Listen for scroll events
    window.addEventListener('scroll', requestTick, { passive: true });
    
    const navbarLinks = navbar.querySelectorAll('a[href^="#"]');
    navbarLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            const href = link.getAttribute('href');
            const targetElement = document.querySelector(href);
            
            if (targetElement) {
                e.preventDefault();
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    updateNavbar();
}
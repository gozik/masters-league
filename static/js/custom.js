// You can add any custom JavaScript here
console.log("Tennis Ratings app loaded");

// Example: Add active class to nav links based on current page
document.addEventListener('DOMContentLoaded', function() {
    const currentPath = window.location.pathname;
    document.querySelectorAll('.nav-link').forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
});
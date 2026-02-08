// Auth page JavaScript
let currentForm = 'register';

function showRegister() {
    hideAllForms();
    document.getElementById('registerForm').classList.add('active');
    currentForm = 'register';
}

function showLogin() {
    hideAllForms();
    document.getElementById('loginForm').classList.add('active');
    currentForm = 'login';
}

function showForgot() {
    hideAllForms();
    document.getElementById('forgotForm').classList.add('active');
    currentForm = 'forgot';
}

function hideAllForms() {
    document.querySelectorAll('.form').forEach(form => {
        form.classList.remove('active');
    });
}

// Travel quotes for inspiration
const quotes = [
    "The world is a book, and those who do not travel read only one page.",
    "Travel is the only thing you buy that makes you richer.",
    "Adventure is worthwhile in itself.",
    "To travel is to take a journey into yourself.",
    "The journey not the arrival matters.",
    "Travel far enough, you meet yourself.",
    "Collect moments, not things.",
    "Life is short and the world is wide."
];

function displayRandomQuote() {
    const quoteElement = document.getElementById('quote');
    if (quoteElement) {
        const randomQuote = quotes[Math.floor(Math.random() * quotes.length)];
        quoteElement.textContent = `"${randomQuote}"`;
    }
}

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    displayRandomQuote();
    showRegister(); // Default to register form
});
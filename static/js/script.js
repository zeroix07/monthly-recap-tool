document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('uploadForm');
    const spinnerOverlay = document.getElementById('spinner-overlay');

    // Show the spinner overlay when the form is submitted
    form.addEventListener('submit', function() {
        spinnerOverlay.style.display = 'flex';  // Show the spinner overlay
    });
});

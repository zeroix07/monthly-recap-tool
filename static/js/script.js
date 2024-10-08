document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('uploadForm');
    const spinnerOverlay = document.getElementById('spinner-overlay');
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('fileInput');
    const fileNameDisplay = document.getElementById('fileName');  // The file name display element
    const dropMessage = document.getElementById('dropMessage');   // The drop zone message

    // Modal elements
    const modal = document.getElementById('modal');
    const closeBtn = document.querySelector('.close-btn');

    // Show the spinner overlay when the form is submitted, but only if a file is selected
    form.addEventListener('submit', function(e) {
        if (!fileInput.files.length) {
            e.preventDefault();  // Prevent the form submission if no file is selected
            modal.style.display = 'flex';  // Show the modal
        } else {
            spinnerOverlay.style.display = 'flex';  // Show the spinner overlay
        }
    });

    // Close the modal when the user clicks on the close button
    closeBtn.addEventListener('click', function() {
        modal.style.display = 'none';  // Hide the modal
    });

    // Also close the modal if the user clicks anywhere outside of the modal content
    window.addEventListener('click', function(e) {
        if (e.target == modal) {
            modal.style.display = 'none';  // Hide the modal
        }
    });

    // Drag-and-drop functionality
    dropZone.addEventListener('click', function() {
        fileInput.click();  // Open file dialog when drop zone is clicked
    });

    dropZone.addEventListener('dragover', function(e) {
        e.preventDefault();
        dropZone.classList.add('dragover');  // Add a class to style the drag-over effect
    });

    dropZone.addEventListener('dragleave', function() {
        dropZone.classList.remove('dragover');  // Remove the class when file is no longer dragged over
    });

    dropZone.addEventListener('drop', function(e) {
        e.preventDefault();
        dropZone.classList.remove('dragover');  // Remove the class when file is dropped
        const files = e.dataTransfer.files;

        // Check if a file was dropped and it's a CSV (check by file extension)
        if (files.length && files[0].name.endsWith('.csv')) {
            // Assign the dropped file to the input element
            fileInput.files = files;
            console.log('File successfully dropped:', files[0].name);

            // Show the file name in the file name display element
            fileNameDisplay.textContent = `File: ${files[0].name}`;

            // Hide the drop message
            dropMessage.style.display = 'none';
        } else {
            alert('Please drop a valid CSV file.');
        }
    });

    // Handle when a file is selected using the file dialog
    fileInput.addEventListener('change', function() {
        if (fileInput.files.length) {
            // Show the file name in the file name display element
            fileNameDisplay.textContent = `File: ${fileInput.files[0].name}`;

            // Hide the drop message
            dropMessage.style.display = 'none';
        }
    });
});

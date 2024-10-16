    document.addEventListener('DOMContentLoaded', function() {
        const dropZone = document.getElementById('drop-zone');
        const fileInput = document.getElementById('uploadFiles');
        const fileNamesDiv = document.getElementById('file-names');  // Element to display the file names

        // Function to display the file names
        function displayFileNames(files) {
            fileNamesDiv.innerHTML = '';  // Clear any previous file names
            if (files.length > 0) {
                let fileList = '<ul>';
                for (let i = 0; i < files.length; i++) {
                    fileList += `<li>${files[i].name}</li>`;  // List each file name
                }
                fileList += '</ul>';
                fileNamesDiv.innerHTML = fileList;  // Update the file names div
            } else {
                fileNamesDiv.innerHTML = '<p>No files selected</p>';  // Display when no files are selected
            }
        }

        // Handle file drag and drop events
        dropZone.addEventListener('dragover', function(e) {
            e.preventDefault();
            dropZone.classList.add('drop-zone--over');
        });

        dropZone.addEventListener('dragleave', function(e) {
            dropZone.classList.remove('drop-zone--over');
        });

        dropZone.addEventListener('drop', function(e) {
            e.preventDefault();
            dropZone.classList.remove('drop-zone--over');
            
            // Handle dropped files
            if (e.dataTransfer.files.length) {
                fileInput.files = e.dataTransfer.files;
                displayFileNames(e.dataTransfer.files);  // Display the file names after dropping
            }
        });

        // Handle click on drop zone to select files
        dropZone.addEventListener('click', function() {
            fileInput.click();
        });

        // Handle file selection via input
        fileInput.addEventListener('change', function() {
            displayFileNames(fileInput.files);  // Display the file names after selecting
        });
    });

    function validateForm() {
        const reportVersion = document.getElementById('reportVersion').value;
    
        if (reportVersion === 'select-the-option') {
            alert('Please select a valid report version.');
            return false;  // Prevent the form from being submitted
        }
    
        return true;  // Allow the form submission if validation passes
    }
    


    
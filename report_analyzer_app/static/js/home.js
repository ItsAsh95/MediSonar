// medical-assistant/report_analyzer_app/static/js/home.js
document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('fileInput');
    const dropzoneArea = document.getElementById('dropzoneArea');
    const browseButton = document.getElementById('browseButton');
    const filePreview = document.getElementById('filePreview');
    const fileNameDisplay = document.getElementById('fileName');
    const fileSizeDisplay = document.getElementById('fileSize');
    const removeFileButton = document.getElementById('removeFileButton');
    const uploadButton = document.getElementById('uploadButton');
    const errorMessageDisplay = document.getElementById('errorMessage');
    const loadingIndicator = document.getElementById('loadingIndicator');

    let currentFile = null;
    const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

    function displayError(message) {
        if(errorMessageDisplay) {
            errorMessageDisplay.textContent = message;
            errorMessageDisplay.style.display = 'block';
        } else { console.error("Error display element not found:", message); }
    }

    function clearError() {
        if(errorMessageDisplay) {
            errorMessageDisplay.textContent = '';
            errorMessageDisplay.style.display = 'none';
        }
    }

    function handleFile(file) {
        clearError();
        if (!file) {
            currentFile = null;
            if(filePreview) filePreview.style.display = 'none';
            if(uploadButton) uploadButton.disabled = true;
            return;
        }

        // Looser check for .txt as type might be octet-stream for text files
        // The backend handles more robust type checking.
        const allowedExtensions = ['.pdf', '.jpg', '.jpeg', '.png', '.txt', '.rtf', '.tiff', '.bmp', '.gif', '.webp'];
        const fileNameLower = file.name.toLowerCase();
        const hasAllowedExtension = allowedExtensions.some(ext => fileNameLower.endsWith(ext));

        if (!hasAllowedExtension) {
            displayError(`Invalid file type: ${file.name}. Please upload PDF, common image formats, or TXT.`);
            currentFile = null;
            if(filePreview) filePreview.style.display = 'none';
            if(uploadButton) uploadButton.disabled = true;
            if(fileInput) fileInput.value = ''; // Clear the input
            return;
        }

        if (file.size > MAX_FILE_SIZE) {
            displayError('File is too large. Maximum size is 10MB.');
            currentFile = null;
            if(filePreview) filePreview.style.display = 'none';
            if(uploadButton) uploadButton.disabled = true;
            if(fileInput) fileInput.value = ''; // Clear the input
            return;
        }

        currentFile = file;
        if(fileNameDisplay) fileNameDisplay.textContent = file.name;
        if(fileSizeDisplay) fileSizeDisplay.textContent = `(${(file.size / 1024).toFixed(0)} KB)`;
        if(filePreview) filePreview.style.display = 'block'; // Changed from 'flex' if not needed
        if(uploadButton) uploadButton.disabled = false;
    }

    if (dropzoneArea && fileInput) {
        dropzoneArea.addEventListener('click', () => fileInput.click());
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropzoneArea.addEventListener(eventName, preventDefaults, false);
        });
        dropzoneArea.addEventListener('dragenter', () => dropzoneArea.classList.add('drag-active'));
        dropzoneArea.addEventListener('dragleave', () => dropzoneArea.classList.remove('drag-active'));
        dropzoneArea.addEventListener('drop', (event) => {
            dropzoneArea.classList.remove('drag-active');
            const dt = event.dataTransfer;
            const files = dt.files;
            if (files && files.length > 0) {
                fileInput.files = files; 
                handleFile(files[0]);
            }
        });
    }
    if (browseButton && fileInput) browseButton.addEventListener('click', (e) => {
      e.stopPropagation(); 
      fileInput.click();
    });
    if (fileInput) fileInput.addEventListener('change', (event) => {
        if (event.target.files && event.target.files.length > 0) {
            handleFile(event.target.files[0]);
        }
    });

    if (removeFileButton && fileInput && filePreview && uploadButton) {
        removeFileButton.addEventListener('click', () => {
            currentFile = null;
            fileInput.value = ''; 
            filePreview.style.display = 'none';
            uploadButton.disabled = true;
            clearError();
        });
    }

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    if (uploadButton && loadingIndicator) {
        uploadButton.addEventListener('click', async () => {
            if (!currentFile) {
                displayError('Please select a file to upload.');
                return;
            }
            clearError();
            uploadButton.disabled = true;
            loadingIndicator.style.display = 'flex'; 
            const loaderIcon = document.getElementById('loader-icon-upload')?.firstChild; // Assuming icon is first child
            if (loaderIcon && loaderIcon.classList) loaderIcon.classList.add('animate-spin');

            try {
                const response = await uploadReport(currentFile); // From shared.js
                if (response && response.id) {
                    // MODIFIED Navigation Path to include app prefix
                    window.location.href = `/report-analyzer/analysis/${response.id}`;
                } else {
                    throw new Error("Upload response did not include an analysis ID.");
                }
            } catch (error) {
                console.error('Upload error:', error);
                displayError(error.message || 'Failed to upload the file. Please try again.');
                uploadButton.disabled = false; 
            } finally {
                // loadingIndicator.style.display = 'none'; // Keep showing if navigating
                // if (loaderIcon && loaderIcon.classList) loaderIcon.classList.remove('animate-spin');
                // Do not re-enable button here if navigation is successful
            }
        });
    } else {
        console.warn("Report App (home.js): Upload button or loading indicator not found.");
    }
});
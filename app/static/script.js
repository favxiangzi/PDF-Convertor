// DOM Elements
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const fileName = document.getElementById('fileName');
const translateBtn = document.getElementById('translateBtn');
const resultSection = document.getElementById('resultSection');
const resultMessage = document.getElementById('resultMessage');
const downloadBtn = document.getElementById('downloadBtn');

let selectedFile = null;

// Drag and drop handlers
dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('dragover');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
});

// File input change handler
fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFile(e.target.files[0]);
    }
});

// Handle selected file
function handleFile(file) {
    if (!file.type.includes('pdf')) {
        alert('Please select a PDF file');
        return;
    }
    
    selectedFile = file;
    fileName.textContent = `Selected: ${file.name}`;
    translateBtn.disabled = false;
    resultSection.style.display = 'none';
}

// Translate button click handler
translateBtn.addEventListener('click', async () => {
    if (!selectedFile) return;
    
    console.log('Starting translation for:', selectedFile.name);
    
    // Show loading state
    const btnText = translateBtn.querySelector('.btn-text');
    const btnLoading = translateBtn.querySelector('.btn-loading');
    btnText.style.display = 'none';
    btnLoading.style.display = 'inline';
    translateBtn.disabled = true;
    
    // Set a timeout to show progress message
    let progressMessage = null;
    const progressTimeout = setTimeout(() => {
        progressMessage = document.createElement('p');
        progressMessage.textContent = 'Translating... This may take a moment for large files.';
        progressMessage.style.color = '#666';
        progressMessage.style.marginTop = '10px';
        resultSection.parentNode.insertBefore(progressMessage, resultSection);
    }, 3000);
    
    try {
        const formData = new FormData();
        formData.append('file', selectedFile);
        
        console.log('Sending request to /translate');
        const response = await fetch('/translate', {
            method: 'POST',
            body: formData
        });
        
        clearTimeout(progressTimeout);
        if (progressMessage) progressMessage.remove();
        
        console.log('Response status:', response.status);
        
        if (!response.ok) {
            throw new Error('Server error: ' + response.status);
        }
        
        const result = await response.json();
        console.log('Result:', result);
        
        if (result.success) {
            // Show success message
            resultMessage.textContent = result.message;
            resultSection.style.display = 'block';
            
            // Setup download button
            downloadBtn.href = `/download/${result.output_file}`;
            downloadBtn.download = result.output_file;
            
            console.log('Download URL:', downloadBtn.href);
        } else {
            alert('Error: ' + result.detail);
        }
        
    } catch (error) {
        clearTimeout(progressTimeout);
        if (progressMessage) progressMessage.remove();
        console.error('Error:', error);
        alert('An error occurred: ' + error.message);
    } finally {
        // Reset button state
        btnText.style.display = 'inline';
        btnLoading.style.display = 'none';
        translateBtn.disabled = false;
    }
});
document.addEventListener('DOMContentLoaded', function() {
    // Chapter selection functionality
    const selectAllBtn = document.getElementById('select-all');
    const deselectAllBtn = document.getElementById('deselect-all');
    const chapterCheckboxes = document.querySelectorAll('.chapter-checkbox');
    
    if (selectAllBtn) {
        selectAllBtn.addEventListener('click', function() {
            chapterCheckboxes.forEach(checkbox => {
                checkbox.checked = true;
            });
        });
    }
    
    if (deselectAllBtn) {
        deselectAllBtn.addEventListener('click', function() {
            chapterCheckboxes.forEach(checkbox => {
                checkbox.checked = false;
            });
        });
    }
    
    // Copy URLs functionality
    const copyAllBtns = document.querySelectorAll('.copy-all-btn');
    copyAllBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const chapterId = this.getAttribute('data-chapter');
            const textarea = document.getElementById(`urls-${chapterId}`);
            
            if (textarea) {
                textarea.select();
                document.execCommand('copy');
                
                // Show copied message
                const originalText = this.textContent;
                this.textContent = 'Copied!';
                this.classList.add('btn-success');
                this.classList.remove('btn-outline-primary');
                
                setTimeout(() => {
                    this.textContent = originalText;
                    this.classList.remove('btn-success');
                    this.classList.add('btn-outline-primary');
                }, 2000);
            }
        });
    });
    
    // Preview functionality
    const previewBtns = document.querySelectorAll('.preview-btn');
    const previewModal = document.getElementById('previewModal') ? new bootstrap.Modal(document.getElementById('previewModal'), {}) : null;
    const loadingSpinner = document.getElementById('loadingSpinner');
    const previewContent = document.getElementById('previewContent');
    const imageCount = document.getElementById('imageCount');
    const previewImages = document.getElementById('previewImages');
    const previewError = document.getElementById('previewError');
    
    if (previewBtns.length > 0 && previewModal) {
        previewBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const chapterUrl = this.getAttribute('data-chapter-url');
                
                // Reset modal state
                loadingSpinner.classList.remove('d-none');
                previewContent.classList.add('d-none');
                previewError.classList.add('d-none');
                previewImages.innerHTML = '';
                
                // Show modal
                previewModal.show();
                
                // Fetch chapter images
                fetch('/api/extract_single_chapter', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ chapter_url: chapterUrl }),
                })
                .then(response => response.json())
                .then(data => {
                    loadingSpinner.classList.add('d-none');
                    
                    if (data.success && data.image_urls && data.image_urls.length > 0) {
                        previewContent.classList.remove('d-none');
                        imageCount.textContent = data.image_urls.length;
                        
                        // Only display the first 6 images in preview
                        const imagesToShow = data.image_urls.slice(0, 6);
                        
                        // Add images to preview
                        imagesToShow.forEach((imageUrl, index) => {
                            const col = document.createElement('div');
                            col.className = 'col-md-4 mb-3';
                            
                            col.innerHTML = `
                                <div class="card">
                                    <div class="card-body p-2 text-center">
                                        <p class="small">Image #${index + 1}</p>
                                        <a href="${imageUrl}" target="_blank" class="btn btn-sm btn-outline-secondary">View Full Size</a>
                                    </div>
                                </div>
                            `;
                            
                            previewImages.appendChild(col);
                        });
                        
                        // Show message if more images are available
                        if (data.image_urls.length > 6) {
                            const moreInfo = document.createElement('div');
                            moreInfo.className = 'col-12 text-center mt-2';
                            moreInfo.innerHTML = `<p class="text-info">${data.image_urls.length - 6} more images available. Extract this chapter to see all.</p>`;
                            previewImages.appendChild(moreInfo);
                        }
                    } else {
                        previewError.classList.remove('d-none');
                        previewError.textContent = data.error || 'No images found in this chapter.';
                    }
                })
                .catch(error => {
                    loadingSpinner.classList.add('d-none');
                    previewError.classList.remove('d-none');
                    previewError.textContent = 'Error loading chapter preview: ' + error.message;
                });
            });
        });
    }
    
    // Convert to HTML functionality
    const convertToHtmlBtns = document.querySelectorAll('.convert-to-html-btn');
    convertToHtmlBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const chapterId = this.getAttribute('data-chapter');
            const urlsTextarea = document.getElementById(`urls-${chapterId}`);
            const htmlContainer = document.getElementById(`html-output-${chapterId}`);
            const htmlTextarea = document.getElementById(`html-${chapterId}`);
            const removeLogoSwitch = document.getElementById(`remove-logo-${chapterId}`);
            
            if (urlsTextarea && htmlTextarea) {
                // Get image URLs
                const urls = urlsTextarea.value.split('\n').filter(url => url.trim() !== '');
                
                // Generate HTML
                generateHtmlFromUrls(urls, htmlTextarea, removeLogoSwitch.checked);
                
                // Show HTML container
                htmlContainer.style.display = 'block';
                
                // Update button text
                this.textContent = 'Update HTML';
            }
        });
    });
    
    // Remove logo switch functionality
    const removeLogoSwitches = document.querySelectorAll('.remove-logo-switch');
    removeLogoSwitches.forEach(switchElem => {
        switchElem.addEventListener('change', function() {
            const chapterId = this.getAttribute('data-chapter');
            const urlsTextarea = document.getElementById(`urls-${chapterId}`);
            const htmlTextarea = document.getElementById(`html-${chapterId}`);
            
            if (urlsTextarea && htmlTextarea) {
                // Get image URLs
                const urls = urlsTextarea.value.split('\n').filter(url => url.trim() !== '');
                
                // Generate HTML
                generateHtmlFromUrls(urls, htmlTextarea, this.checked);
            }
        });
    });
    
    // Copy HTML functionality
    const copyHtmlBtns = document.querySelectorAll('.copy-html-btn');
    copyHtmlBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const chapterId = this.getAttribute('data-chapter');
            const htmlTextarea = document.getElementById(`html-${chapterId}`);
            
            if (htmlTextarea) {
                htmlTextarea.select();
                document.execCommand('copy');
                
                // Show copied message
                const originalText = this.textContent;
                this.textContent = 'Copied!';
                this.classList.add('btn-success');
                this.classList.remove('btn-outline-primary');
                
                setTimeout(() => {
                    this.textContent = originalText;
                    this.classList.remove('btn-success');
                    this.classList.add('btn-outline-primary');
                }, 2000);
            }
        });
    });
    
    // Helper function to generate HTML from URLs
    function generateHtmlFromUrls(urls, targetTextarea, removeLogo = false) {
        let html = '';
        let pageCount = 1;
        
        urls.forEach(url => {
            // Skip logo URLs if the option is selected
            if (removeLogo && url.toLowerCase().includes('logo.png')) {
                return;
            }
            
            html += `<img src="${url.trim()}" alt="Page ${pageCount}" class="img-fluid mb-2">\n`;
            pageCount++;
        });
        
        targetTextarea.value = html;
    }
    
    // Add back button for rollback functionality
    const backBtn = document.querySelector('a[href="/"]');
    if (backBtn) {
        backBtn.addEventListener('click', function(e) {
            // If there are results, ask for confirmation
            const resultsSection = document.querySelector('.accordion');
            if (resultsSection) {
                const confirmed = confirm("Are you sure you want to go back? This will clear current results and allow you to scrape another manga.");
                if (!confirmed) {
                    e.preventDefault();
                }
            }
        });
    }
});

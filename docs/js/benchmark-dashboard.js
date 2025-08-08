class BenchmarkDashboard {
    constructor() {
        this.data = {};
        this.manifest = {};
        this.modelLinks = {};
        this.router = new URLRouter();
        this.router.onViewChange = (view, params) => this.handleViewChange(view, params);
        this.fileLoader = new IndividualFileLoader((url, timeout) => this.fetchWithTimeout(url, timeout));
        this.init();
    }

    async init() {
        const loadingHtml = '<div class="loading">Loading data...</div>';
        document.getElementById('model-averages').innerHTML = loadingHtml;
        document.getElementById('results-container').innerHTML = loadingHtml;

        try {
            await this.loadData();
            await this.loadModelLinks();

            // Handle initial view based on URL
            const currentView = this.router.getCurrentView();
            const params = this.router.getParams();
            this.handleViewChange(currentView, params);

        } catch (error) {
            console.error('Error loading data:', error);
            const errorHtml = `<div style="color: red; padding: 20px;">Error: ${error.message}</div>`;
            document.getElementById('model-averages').innerHTML = errorHtml;
            document.getElementById('results-container').innerHTML = errorHtml;
        }
    }

    handleViewChange(view, params) {
        if (view === 'details' && params.category && params.subcategory) {
            this.showDetailsView(params.category, params.subcategory);
        } else {
            this.showDashboardView();
        }
    }

    showDashboardView() {
        // Clean up any sticky headers from details view
        this.cleanupStickyHeaders();

        // Show main dashboard sections
        document.getElementById('model-averages').style.display = 'block';
        document.getElementById('results-container').style.display = 'block';

        // Hide details view (will be created later)
        const detailsView = document.getElementById('details-view');
        if (detailsView) {
            detailsView.style.display = 'none';
        }

        // Render dashboard content
        this.renderModelAverages();
        this.renderResults();
    }

    async showDetailsView(category, subcategory) {
        // Hide dashboard sections
        document.getElementById('results-container').style.display = 'none';

        // Show details view
        const detailsView = document.getElementById('details-view');
        detailsView.style.display = 'block';

        // Update breadcrumb and title
        document.getElementById('breadcrumb-path').textContent = `${category} > ${subcategory}`;
        document.getElementById('details-title').textContent = `${subcategory} - Detailed Results`;

        // Show loading state
        document.getElementById('details-content').innerHTML = '<div class="loading">Loading detailed results...</div>';

        try {
            await this.loadAndRenderDetails(category, subcategory);
        } catch (error) {
            console.error('Error loading details:', error);
            document.getElementById('details-content').innerHTML =
                `<div style="color: red; padding: 20px;">Error loading details: ${error.message}</div>`;
        }
    }

    async loadAndRenderDetails(category, subcategory) {
        // Get individual files from manifest
        const subcategoryInfo = this.manifest.structure[category]?.[subcategory];
        if (!subcategoryInfo || !subcategoryInfo.individual_files) {
            throw new Error('No individual files found for this category');
        }

        const individualFiles = subcategoryInfo.individual_files;

        // Load individual files
        const loadResults = await this.fileLoader.loadIndividualFiles(individualFiles);

        // Handle any loading errors
        this.fileLoader.handleLoadingErrors(loadResults.failed);

        if (loadResults.successful.length === 0) {
            throw new Error('No individual files could be loaded');
        }

        // Render the details
        this.renderDetailsContent(loadResults.data, category, subcategory);

        // Set up filtering
        this.setupDetailsControls(loadResults.data);
    }

    renderDetailsContent(imageData, category, subcategory) {
        const imageFiles = Object.values(imageData);

        if (imageFiles.length === 0) {
            document.getElementById('details-content').innerHTML =
                '<div class="no-data">No image data available</div>';
            return;
        }

        // Store the original data for sorting
        this.currentImageData = imageFiles;

        // Apply current sorting
        const sortedImageFiles = this.sortImageFiles(imageFiles);

        let html = '';

        sortedImageFiles.forEach(imageResult => {
            html += this.renderImageResult(imageResult);
        });

        document.getElementById('details-content').innerHTML = html;
    }

    renderImageResult(imageResult) {
        const { filename, models } = imageResult;
        const modelNames = Object.keys(models);

        if (modelNames.length === 0) {
            return `<div class="image-result">
                <div class="image-result-header" onclick="dashboard.toggleImageResult(this)">
                    <div class="image-result-title">
                        <span class="image-name">
                            ${filename}
                            ${this.createImageIcon(filename)}
                        </span>
                        <span class="average-accuracy no-data">No data</span>
                    </div>
                </div>
                <div class="image-result-content">
                    <p>No model results available</p>
                </div>
            </div>`;
        }

        // Calculate average accuracy across all models
        const accuracies = modelNames.map(modelName => models[modelName].accuracy);
        const averageAccuracy = accuracies.reduce((sum, acc) => sum + acc, 0) / accuracies.length;

        // Get color class based on accuracy thresholds
        const accuracyColorClass = this.getAccuracyColorClass(averageAccuracy);

        // Get ground truth from first model (should be same for all)
        const groundTruth = models[modelNames[0]].groundTruth;

        let html = `
            <div class="image-result" data-filename="${filename}">
                <div class="image-result-header" onclick="dashboard.toggleImageResult(this)">
                    <div class="image-result-title">
                        <span class="image-name">
                            ${filename}
                            ${this.createImageIcon(filename)}
                        </span>
                        <span class="average-accuracy ${accuracyColorClass}">${averageAccuracy.toFixed(1)}%</span>
                    </div>
                </div>
                
                <div class="image-result-content">
                    <div class="ground-truth">
                        <h4>Ground Truth:</h4>
                        <div class="ground-truth-text">${this.escapeHtml(groundTruth)}</div>
                    </div>
                    
                    <div class="model-responses">`;

        // Sort models by accuracy (highest first)
        const sortedModels = modelNames.sort((a, b) =>
            models[b].accuracy - models[a].accuracy
        );

        sortedModels.forEach(modelName => {
            const modelData = models[modelName];
            html += this.renderModelResponse(modelName, modelData, groundTruth);
        });

        html += `
                    </div>
                </div>
            </div>`;

        return html;
    }

    renderModelResponse(modelName, modelData, groundTruth) {
        const { response, wer, cer, accuracy, time } = modelData;

        return `
            <div class="model-response" data-model="${modelName}">
                <h5>
                    ${this.formatModelName(modelName)}
                    <button class="diff-button" onclick="dashboard.toggleDiff(this, '${this.escapeHtml(groundTruth)}', '${this.escapeHtml(response)}')">
                        Show Diff
                    </button>
                </h5>
                
                <div class="model-metrics">
                    <span class="metric">Accuracy: ${accuracy.toFixed(1)}%</span>
                    <span class="metric">CER: ${cer.toFixed(1)}%</span>
                    <span class="metric">WER: ${wer.toFixed(1)}%</span>
                    <span class="metric">Time: ${time.toFixed(2)}s</span>
                </div>
                
                <div class="model-response-text">${this.escapeHtml(response)}</div>
                <div class="diff-container" style="display: none;"></div>
            </div>`;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    getAccuracyColorClass(accuracy) {
        if (accuracy < 50) return 'accuracy-very-low';      // <50% dark red
        if (accuracy < 75) return 'accuracy-low';           // 50-75% red
        if (accuracy < 85) return 'accuracy-medium';        // 75-85% yellow
        if (accuracy < 95) return 'accuracy-good';          // 85-95% light green
        return 'accuracy-excellent';                        // 95-100% dark green
    }

    sortImageFiles(imageFiles) {
        const sortBy = document.getElementById('sort-by')?.value || 'filename-asc';

        return [...imageFiles].sort((a, b) => {
            switch (sortBy) {
                case 'filename-asc':
                    return a.filename.localeCompare(b.filename);
                case 'filename-desc':
                    return b.filename.localeCompare(a.filename);
                case 'accuracy-desc':
                    return this.calculateAverageAccuracy(b) - this.calculateAverageAccuracy(a);
                case 'accuracy-asc':
                    return this.calculateAverageAccuracy(a) - this.calculateAverageAccuracy(b);
                default:
                    return 0;
            }
        });
    }

    calculateAverageAccuracy(imageResult) {
        const modelNames = Object.keys(imageResult.models);
        if (modelNames.length === 0) return 0;

        const accuracies = modelNames.map(modelName => imageResult.models[modelName].accuracy);
        return accuracies.reduce((sum, acc) => sum + acc, 0) / accuracies.length;
    }

    createImageIcon(filename) {
        // Get current view parameters to construct image path
        const params = this.router.getParams();
        if (!params.category || !params.subcategory) {
            return ''; // Only show icon in details view
        }

        // Extract base filename (e.g., "00082" from "00082.bin")
        const baseFilename = filename.split('.')[0];

        // Construct image path: data/images/EarlyModernLatin/1471-Orthographia-Tortellius/00082.webp
        const imagePath = `data/images/${params.category}/${params.subcategory}/${baseFilename}.webp`;

        // Debug: log the constructed path
        console.log(`Image path for ${filename} -> ${baseFilename}: ${imagePath}`);

        return `
            <div class="image-icon-container">
                <svg class="image-icon" viewBox="0 0 24 24" width="16" height="16">
                    <path fill="currentColor" d="M21,19V5c0,-1.1 -0.9,-2 -2,-2H5c-1.1,0 -2,0.9 -2,2v14c1.1,0 2,-0.9 2,-2zM8.5,13.5l2.5,3.01L14.5,12l4.5,6H5l3.5,-4.5z"/>
                </svg>
                <div class="image-tooltip">
                    <img src="${imagePath}" alt="Ground truth image: ${filename}" loading="lazy" onerror="console.error('Failed to load image:', this.src)" />
                </div>
            </div>
        `;
    }

    toggleImageResult(headerElement) {
        const content = headerElement.nextElementSibling;
        content.classList.toggle('show');
        headerElement.classList.toggle('expanded');
    }

    getImageCount(categoryName, subcategoryName) {
        // Try to get image count from manifest first (most up-to-date)
        if (this.manifest &&
            this.manifest.structure &&
            this.manifest.structure[categoryName] &&
            this.manifest.structure[categoryName][subcategoryName] &&
            this.manifest.structure[categoryName][subcategoryName].image_count) {
            return this.manifest.structure[categoryName][subcategoryName].image_count;
        }

        // Fallback to aggregated data if manifest doesn't have it
        if (this.data[categoryName] &&
            this.data[categoryName][subcategoryName] &&
            Object.values(this.data[categoryName][subcategoryName]).length > 0) {
            return Object.values(this.data[categoryName][subcategoryName])[0].images;
        }

        // Default fallback
        return 0;
    }

    getTotalImagesFromManifest() {
        let totalImages = 0;

        if (this.manifest && this.manifest.structure) {
            // Sum up all image counts from manifest
            Object.values(this.manifest.structure).forEach(category => {
                Object.values(category).forEach(subcategory => {
                    if (subcategory.image_count) {
                        totalImages += subcategory.image_count;
                    }
                });
            });
        }

        // Fallback to aggregated data if manifest doesn't have counts
        if (totalImages === 0) {
            Object.values(this.data).forEach(category => {
                Object.values(category).forEach(subcategory => {
                    if (Object.values(subcategory).length > 0) {
                        totalImages += Object.values(subcategory)[0].images;
                    }
                });
            });
        }

        return totalImages;
    }

    async fetchWithTimeout(url, timeout = 5000) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);

        try {
            // Add cache-busting parameter to ensure fresh data
            const cacheBustUrl = url + (url.includes('?') ? '&' : '?') + '_t=' + Date.now();
            const response = await fetch(cacheBustUrl, {
                signal: controller.signal,
                cache: 'no-cache',
                headers: {
                    'Cache-Control': 'no-cache, no-store, must-revalidate',
                    'Pragma': 'no-cache',
                    'Expires': '0'
                }
            });
            clearTimeout(timeoutId);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText} for ${url}`);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            clearTimeout(timeoutId);
            if (error.name === 'AbortError') {
                throw new Error(`Timeout loading ${url}`);
            }
            throw error;
        }
    }

    async loadData() {
        try {
            // Load the manifest file that lists JSON files
            const manifest = await this.fetchWithTimeout('data/json/manifest.json');
            this.manifest = manifest;

            // Update last update timestamp
            if (manifest.generated) {
                const date = new Date(manifest.generated);
                document.getElementById('last-update').textContent = date.toLocaleString();
            }

            if (!manifest.files || manifest.files.length === 0) {
                throw new Error('No files listed in manifest');
            }

            // Try to load each file listed in the manifest
            const loadPromises = manifest.files.map(async filename => {
                try {
                    const data = await this.fetchWithTimeout(`data/json/${filename}`);
                    return { filename, data, success: true };
                } catch (error) {
                    return { filename, error: error.message, success: false };
                }
            });

            const results = await Promise.all(loadPromises);
            const successful = results.filter(r => r.success);
            const failed = results.filter(r => !r.success);

            if (successful.length === 0) {
                throw new Error('No JSON files could be loaded from the manifest');
            }

            // Organize data using the manifest structure
            this.data = {};

            // Use the structure from manifest if available, otherwise organize by filename
            if (manifest.structure) {
                // Initialize categories from manifest
                Object.keys(manifest.structure).forEach(categoryName => {
                    this.data[categoryName] = {};
                });

                // Place loaded data into appropriate categories
                successful.forEach(({ filename, data }) => {
                    // Extract just the final part of the path (e.g., "1471-Orthographia-Tortellius" from "GT4HistOCR/corpus/EarlyModernLatin/1471-Orthographia-Tortellius.json")
                    const nameWithoutExt = filename.split('/').pop().replace('.json', '');
                    let placed = false;

                    // Try to find the right category from manifest structure
                    Object.entries(manifest.structure).forEach(([categoryName, subcategories]) => {
                        // Handle both old format (array) and new format (object)
                        const subcategoryNames = Array.isArray(subcategories)
                            ? subcategories
                            : Object.keys(subcategories);

                        if (subcategoryNames.includes(nameWithoutExt)) {
                            this.data[categoryName][nameWithoutExt] = data;
                            placed = true;
                        }
                    });

                    // If not found in manifest structure, use default category
                    if (!placed) {
                        const defaultCategory = 'EarlyModernLatin';
                        if (!this.data[defaultCategory]) {
                            this.data[defaultCategory] = {};
                        }
                        this.data[defaultCategory][nameWithoutExt] = data;
                    }
                });
            } else {
                // Fallback: organize by filename
                this.data['EarlyModernLatin'] = {};
                successful.forEach(({ filename, data }) => {
                    const nameWithoutExt = filename.split('/').pop().replace('.json', '');
                    this.data['EarlyModernLatin'][nameWithoutExt] = data;
                });
            }

        } catch (error) {
            throw new Error(`Failed to load benchmark data: ${error.message}`);
        }
    }

    async loadModelLinks() {
        try {
            const modelLinks = await this.fetchWithTimeout('data/json/model_links.json');
            this.modelLinks = modelLinks;
        } catch (error) {
            console.warn('Could not load model links:', error.message);
            this.modelLinks = {};
        }
    }

    formatModelName(modelName) {
        if (this.modelLinks[modelName]) {
            return `<a href="${this.modelLinks[modelName]}" target="_blank" rel="noopener noreferrer" class="model-link">${this.escapeHtml(modelName)}</a>`;
        }
        return this.escapeHtml(modelName);
    }

    calculateModelAverages() {
        const modelStats = {};

        // Collect all results for each model
        Object.entries(this.data).forEach(([categoryName, categoryData]) => {
            Object.entries(categoryData).forEach(([subcategoryName, subcategoryData]) => {
                Object.entries(subcategoryData).forEach(([modelName, modelData]) => {
                    if (!modelStats[modelName]) {
                        modelStats[modelName] = {
                            results: [],
                            totalImages: 0,
                            categories: new Set()
                        };
                    }
                    modelStats[modelName].results.push(modelData);
                    modelStats[modelName].categories.add(`${categoryName}/${subcategoryName}`);

                    // Use actual image count for this model (from the processed data)
                    const imageCount = modelData.images || 0;
                    modelStats[modelName].totalImages += imageCount;
                });
            });
        });

        // Calculate weighted averages for each model
        const modelAverages = {};
        Object.entries(modelStats).forEach(([modelName, stats]) => {
            const count = stats.results.length;

            // Calculate weighted averages based on image count
            const weightedTotals = stats.results.reduce((acc, result, index) => {
                // Get the corresponding category/subcategory for this result
                const resultIndex = index;
                const categoryEntries = Object.entries(this.data);
                let imageCount = 0;
                let found = false;

                // Find the image count for this specific result
                for (const [categoryName, categoryData] of categoryEntries) {
                    for (const [subcategoryName, subcategoryData] of Object.entries(categoryData)) {
                        if (subcategoryData[modelName] === result) {
                            imageCount = this.getImageCount(categoryName, subcategoryName);
                            found = true;
                            break;
                        }
                    }
                    if (found) break;
                }

                // Weight each metric by the number of images in that dataset
                acc.wer += result.avg_wer * imageCount;
                acc.cer += result.avg_cer * imageCount;
                acc.accuracy += result.avg_accuracy * imageCount;
                acc.time += result.avg_time * imageCount;
                acc.totalWeight += imageCount;

                return acc;
            }, { wer: 0, cer: 0, accuracy: 0, time: 0, totalWeight: 0 });

            modelAverages[modelName] = {
                avg_wer: weightedTotals.totalWeight > 0 ? weightedTotals.wer / weightedTotals.totalWeight : 0,
                avg_cer: weightedTotals.totalWeight > 0 ? weightedTotals.cer / weightedTotals.totalWeight : 0,
                avg_accuracy: weightedTotals.totalWeight > 0 ? weightedTotals.accuracy / weightedTotals.totalWeight : 0,
                avg_time: weightedTotals.totalWeight > 0 ? weightedTotals.time / weightedTotals.totalWeight : 0,
                totalImages: stats.totalImages,
                benchmarkCount: count
            };
        });

        return modelAverages;
    }

    renderModelAverages() {
        const modelAverages = this.calculateModelAverages();
        if (!modelAverages || Object.keys(modelAverages).length === 0) return;

        // Store model averages for sorting
        this.modelAverages = modelAverages;
        this.currentSort = this.currentSort || { column: 'accuracy', direction: 'desc' };

        this.renderLeaderboardTable();
    }

    renderLeaderboardTable() {
        if (!this.modelAverages) return;

        // Sort models based on current sort settings
        const sortedModels = this.sortModels(this.modelAverages, this.currentSort.column, this.currentSort.direction);

        // Find best scores for highlighting
        const allModels = Object.values(this.modelAverages);
        const best = {
            wer: Math.min(...allModels.map(m => m.avg_wer)),
            cer: Math.min(...allModels.map(m => m.avg_cer)),
            accuracy: Math.max(...allModels.map(m => m.avg_accuracy)),
            time: Math.min(...allModels.map(m => m.avg_time))
        };

        let html = `
            <table class="results-table">
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Model</th>
                        <th class="sortable ${this.currentSort.column === 'accuracy' ? 'sorted-' + this.currentSort.direction : ''}" data-sort="accuracy">
                            Accuracy (%)
                            <span class="sort-indicator">
                                <span class="sort-arrow sort-up ${this.currentSort.column === 'accuracy' && this.currentSort.direction === 'asc' ? 'active' : ''}">▲</span>
                                <span class="sort-arrow sort-down ${this.currentSort.column === 'accuracy' && this.currentSort.direction === 'desc' ? 'active' : ''}">▼</span>
                            </span>
                        </th>
                        <th class="sortable ${this.currentSort.column === 'cer' ? 'sorted-' + this.currentSort.direction : ''}" data-sort="cer">
                            CER (%)
                            <span class="sort-indicator">
                                <span class="sort-arrow sort-up ${this.currentSort.column === 'cer' && this.currentSort.direction === 'asc' ? 'active' : ''}">▲</span>
                                <span class="sort-arrow sort-down ${this.currentSort.column === 'cer' && this.currentSort.direction === 'desc' ? 'active' : ''}">▼</span>
                            </span>
                        </th>
                        <th class="sortable ${this.currentSort.column === 'wer' ? 'sorted-' + this.currentSort.direction : ''}" data-sort="wer">
                            WER (%)
                            <span class="sort-indicator">
                                <span class="sort-arrow sort-up ${this.currentSort.column === 'wer' && this.currentSort.direction === 'asc' ? 'active' : ''}">▲</span>
                                <span class="sort-arrow sort-down ${this.currentSort.column === 'wer' && this.currentSort.direction === 'desc' ? 'active' : ''}">▼</span>
                            </span>
                        </th>
                        <th class="sortable ${this.currentSort.column === 'time' ? 'sorted-' + this.currentSort.direction : ''}" data-sort="time">
                            Time (s)
                            <span class="sort-indicator">
                                <span class="sort-arrow sort-up ${this.currentSort.column === 'time' && this.currentSort.direction === 'asc' ? 'active' : ''}">▲</span>
                                <span class="sort-arrow sort-down ${this.currentSort.column === 'time' && this.currentSort.direction === 'desc' ? 'active' : ''}">▼</span>
                            </span>
                        </th>
                        <th>Total Images</th>
                    </tr>
                </thead>
                <tbody>`;

        sortedModels.forEach(([modelName, modelData], index) => {
            const werClass = modelData.avg_wer === best.wer ? 'best-score' : '';
            const cerClass = modelData.avg_cer === best.cer ? 'best-score' : '';
            const accClass = modelData.avg_accuracy === best.accuracy ? 'best-score' : '';
            const timeClass = modelData.avg_time === best.time ? 'best-score' : '';

            html += `
                <tr>
                    <td class="rank-number">${index + 1}</td>
                    <td class="model-name">${this.formatModelName(modelName)}</td>
                    <td class="${accClass}">${modelData.avg_accuracy.toFixed(2)}</td>
                    <td class="${cerClass}">${modelData.avg_cer.toFixed(2)}</td>
                    <td class="${werClass}">${modelData.avg_wer.toFixed(2)}</td>
                    <td class="${timeClass}">${modelData.avg_time.toFixed(2)}</td>
                    <td>${modelData.totalImages}</td>
                </tr>`;
        });

        html += `
                </tbody>
            </table>`;

        document.getElementById('model-averages').innerHTML = html;
        this.attachSortListeners();
    }

    sortModels(modelAverages, column, direction) {
        const entries = Object.entries(modelAverages);

        return entries.sort(([, a], [, b]) => {
            let valueA, valueB;

            switch (column) {
                case 'accuracy':
                    valueA = a.avg_accuracy;
                    valueB = b.avg_accuracy;
                    break;
                case 'cer':
                    valueA = a.avg_cer;
                    valueB = b.avg_cer;
                    break;
                case 'wer':
                    valueA = a.avg_wer;
                    valueB = b.avg_wer;
                    break;
                case 'time':
                    valueA = a.avg_time;
                    valueB = b.avg_time;
                    break;
                default:
                    return 0;
            }

            if (direction === 'asc') {
                return valueA - valueB;
            } else {
                return valueB - valueA;
            }
        });
    }

    attachSortListeners() {
        const sortableHeaders = document.querySelectorAll('#model-averages .results-table .sortable');

        sortableHeaders.forEach(header => {
            header.addEventListener('click', () => {
                const column = header.getAttribute('data-sort');

                // Toggle direction if same column, otherwise default to desc for accuracy, asc for errors/time
                if (this.currentSort.column === column) {
                    this.currentSort.direction = this.currentSort.direction === 'asc' ? 'desc' : 'asc';
                } else {
                    // For accuracy, default to desc (higher is better)
                    // For CER, WER, and time, default to asc (lower is better)
                    this.currentSort.direction = column === 'accuracy' ? 'desc' : 'asc';
                }

                this.currentSort.column = column;
                this.renderLeaderboardTable();
            });
        });
    }

    attachCategorySortListeners() {
        // Initialize sort state for each category table
        this.categorySorts = this.categorySorts || {};

        const sortableHeaders = document.querySelectorAll('#results-container .results-table .sortable');
        console.log('Found', sortableHeaders.length, 'sortable headers in category tables');

        sortableHeaders.forEach(header => {
            header.addEventListener('click', (event) => {
                event.stopPropagation(); // Prevent event bubbling
                console.log('Category table header clicked:', header.getAttribute('data-sort'));
                const table = header.closest('.results-table');
                const tableId = table.getAttribute('data-table-id');
                const column = header.getAttribute('data-sort');

                // Initialize sort state for this table if not exists
                if (!this.categorySorts[tableId]) {
                    this.categorySorts[tableId] = { column: 'accuracy', direction: 'desc' };
                }

                // Toggle direction if same column, otherwise default to desc for accuracy, asc for errors/time
                if (this.categorySorts[tableId].column === column) {
                    this.categorySorts[tableId].direction = this.categorySorts[tableId].direction === 'asc' ? 'desc' : 'asc';
                } else {
                    // For accuracy, default to desc (higher is better)
                    // For CER, WER, and time, default to asc (lower is better)
                    this.categorySorts[tableId].direction = column === 'accuracy' ? 'desc' : 'asc';
                }

                this.categorySorts[tableId].column = column;
                console.log('Sorting category table:', tableId, 'by', column, this.categorySorts[tableId].direction);
                this.renderCategoryTable(table, tableId);
            });
        });
    }

    renderCategoryTable(table, tableId) {
        const tbody = table.querySelector('tbody');
        const thead = table.querySelector('thead');

        // Get category and subcategory from data attributes
        const categoryName = table.getAttribute('data-category');
        const subcategoryName = table.getAttribute('data-subcategory');

        // Find the subcategory data
        const subcategoryData = this.data[categoryName]?.[subcategoryName];
        if (!subcategoryData) {
            console.error('No subcategory data found for:', categoryName, subcategoryName);
            return;
        }

        console.log('Rendering category table for:', categoryName, subcategoryName, 'with', Object.keys(subcategoryData).length, 'models');

        const sortState = this.categorySorts[tableId];
        const best = this.findBestScores(subcategoryData);

        // Sort the models
        const sortedModels = this.sortModels(subcategoryData, sortState.column, sortState.direction);

        // Update header indicators
        const headers = thead.querySelectorAll('.sortable');
        headers.forEach(header => {
            const headerColumn = header.getAttribute('data-sort');
            const upArrow = header.querySelector('.sort-up');
            const downArrow = header.querySelector('.sort-down');

            // Remove active class from all arrows
            upArrow.classList.remove('active');
            downArrow.classList.remove('active');
            header.classList.remove('sorted-asc', 'sorted-desc');

            // Add active class to current sort
            if (headerColumn === sortState.column) {
                if (sortState.direction === 'asc') {
                    upArrow.classList.add('active');
                    header.classList.add('sorted-asc');
                } else {
                    downArrow.classList.add('active');
                    header.classList.add('sorted-desc');
                }
            }
        });

        // Rebuild tbody
        let html = '';
        sortedModels.forEach(([modelName, modelData], index) => {
            const werClass = modelData.avg_wer === best.wer ? 'best-score' : '';
            const cerClass = modelData.avg_cer === best.cer ? 'best-score' : '';
            const accClass = modelData.avg_accuracy === best.accuracy ? 'best-score' : '';
            const timeClass = modelData.avg_time === best.time ? 'best-score' : '';

            html += `
                <tr>
                    <td class="rank-number">${index + 1}</td>
                    <td class="model-name">${this.formatModelName(modelName)}</td>
                    <td class="${accClass}">${modelData.avg_accuracy.toFixed(2)}</td>
                    <td class="${cerClass}">${modelData.avg_cer.toFixed(2)}</td>
                    <td class="${werClass}">${modelData.avg_wer.toFixed(2)}</td>
                    <td class="${timeClass}">${modelData.avg_time.toFixed(2)}</td>
                    <td>${modelData.images || 0}</td>
                </tr>`;
        });

        tbody.innerHTML = html;
    }

    findBestScores(subcategoryData) {
        const models = Object.keys(subcategoryData);
        const best = {
            wer: Math.min(...models.map(m => subcategoryData[m].avg_wer)),
            cer: Math.min(...models.map(m => subcategoryData[m].avg_cer)),
            accuracy: Math.max(...models.map(m => subcategoryData[m].avg_accuracy)),
            time: Math.min(...models.map(m => subcategoryData[m].avg_time))
        };
        return best;
    }

    renderResults() {
        let html = '';

        Object.entries(this.data).forEach(([categoryName, categoryData]) => {
            html += `<div class="category">
                <div class="category-header">${categoryName}</div>`;

            Object.entries(categoryData).forEach(([subcategoryName, subcategoryData]) => {
                const best = this.findBestScores(subcategoryData);
                const tableId = `table-${categoryName}-${subcategoryName}`.replace(/[^a-zA-Z0-9-]/g, '-');

                html += `
                    <div class="subcategory">
                        <div class="subcategory-header" onclick="this.nextElementSibling.classList.toggle('show'); this.classList.toggle('expanded')">
                            <span class="subcategory-title">${subcategoryName} (${this.getImageCount(categoryName, subcategoryName)} images)</span>
                            <button class="details-button" onclick="event.stopPropagation(); dashboard.navigateToDetails('${categoryName}', '${subcategoryName}')">
                                Details →
                            </button>
                        </div>
                        <div class="model-results">
                            <table class="results-table" data-table-id="${tableId}" data-category="${categoryName}" data-subcategory="${subcategoryName}">
                                <thead>
                                    <tr>
                                        <th>Rank</th>
                                        <th>Model</th>
                                        <th class="sortable" data-sort="accuracy">
                                            Accuracy (%)
                                            <span class="sort-indicator">
                                                <span class="sort-arrow sort-up">▲</span>
                                                <span class="sort-arrow sort-down active">▼</span>
                                            </span>
                                        </th>
                                        <th class="sortable" data-sort="cer">
                                            CER (%)
                                            <span class="sort-indicator">
                                                <span class="sort-arrow sort-up">▲</span>
                                                <span class="sort-arrow sort-down">▼</span>
                                            </span>
                                        </th>
                                        <th class="sortable" data-sort="wer">
                                            WER (%)
                                            <span class="sort-indicator">
                                                <span class="sort-arrow sort-up">▲</span>
                                                <span class="sort-arrow sort-down">▼</span>
                                            </span>
                                        </th>
                                        <th class="sortable" data-sort="time">
                                            Time (s)
                                            <span class="sort-indicator">
                                                <span class="sort-arrow sort-up">▲</span>
                                                <span class="sort-arrow sort-down">▼</span>
                                            </span>
                                        </th>
                                        <th>Total Images</th>
                                    </tr>
                                </thead>
                                <tbody>`;

                // Sort models by accuracy (highest first) - default
                const sortedModels = Object.entries(subcategoryData).sort(([, a], [, b]) => b.avg_accuracy - a.avg_accuracy);

                sortedModels.forEach(([modelName, modelData], index) => {
                    const werClass = modelData.avg_wer === best.wer ? 'best-score' : '';
                    const cerClass = modelData.avg_cer === best.cer ? 'best-score' : '';
                    const accClass = modelData.avg_accuracy === best.accuracy ? 'best-score' : '';
                    const timeClass = modelData.avg_time === best.time ? 'best-score' : '';

                    html += `
                        <tr>
                            <td class="rank-number">${index + 1}</td>
                            <td class="model-name">${this.formatModelName(modelName)}</td>
                            <td class="${accClass}">${modelData.avg_accuracy.toFixed(2)}</td>
                            <td class="${cerClass}">${modelData.avg_cer.toFixed(2)}</td>
                            <td class="${werClass}">${modelData.avg_wer.toFixed(2)}</td>
                            <td class="${timeClass}">${modelData.avg_time.toFixed(2)}</td>
                            <td>${modelData.images || 0}</td>
                        </tr>`;
                });

                html += `
                                </tbody>
                            </table>
                        </div>
                    </div>`;
            });

            html += '</div>';
        });

        document.getElementById('results-container').innerHTML = html;
        this.attachCategorySortListeners();
    }

    // Navigation methods for Details buttons
    navigateToDetails(categoryName, subcategoryName) {
        this.router.navigateTo('details', {
            category: categoryName,
            subcategory: subcategoryName
        });
    }

    navigateBackToDashboard() {
        this.router.navigateTo('dashboard');
    }

    // Diff functionality
    toggleDiff(button, groundTruth, response) {
        const diffContainer = button.closest('.model-response').querySelector('.diff-container');
        const responseText = button.closest('.model-response').querySelector('.model-response-text');

        if (diffContainer.style.display === 'none') {
            // Show diff
            const diff = DiffViewer.generateDiff(groundTruth, response);
            const diffHtml = DiffViewer.renderInlineDiff(diff);
            diffContainer.innerHTML = `<div class="diff-view">${diffHtml}</div>`;
            diffContainer.style.display = 'block';
            responseText.style.display = 'none';
            button.textContent = 'Hide Diff';
        } else {
            // Hide diff
            diffContainer.style.display = 'none';
            responseText.style.display = 'block';
            button.textContent = 'Show Diff';
        }
    }

    // Details controls setup
    setupDetailsControls(imageData) {
        const imageFiles = Object.values(imageData);
        if (imageFiles.length === 0) return;

        // Get all unique models
        const allModels = new Set();
        imageFiles.forEach(imageResult => {
            Object.keys(imageResult.models).forEach(model => allModels.add(model));
        });

        // Populate model filter
        const modelFilter = document.getElementById('model-filter');
        modelFilter.innerHTML = '<option value="">All Models</option>';
        Array.from(allModels).sort().forEach(model => {
            modelFilter.innerHTML += `<option value="${model}">${model}</option>`;
        });

        // Set up event listeners
        modelFilter.addEventListener('change', () => this.applyFilters());

        // Set up sort event listener
        const sortBy = document.getElementById('sort-by');
        if (sortBy) {
            sortBy.addEventListener('change', () => this.applySorting());
        }
    }

    applyFilters() {
        const selectedModel = document.getElementById('model-filter').value;
        const imageResults = document.querySelectorAll('.image-result');

        imageResults.forEach(imageResult => {
            if (!selectedModel) {
                // Show all images and all models
                imageResult.style.display = 'block';
                imageResult.querySelectorAll('.model-response').forEach(response => {
                    response.style.display = 'block';
                });
            } else {
                // Check if this image has data for the selected model
                const selectedModelResponse = imageResult.querySelector(`.model-response[data-model="${selectedModel}"]`);

                if (selectedModelResponse) {
                    // Show the image and only the selected model
                    imageResult.style.display = 'block';
                    imageResult.querySelectorAll('.model-response').forEach(response => {
                        const modelName = response.dataset.model;
                        response.style.display = modelName === selectedModel ? 'block' : 'none';
                    });
                } else {
                    // Hide the entire image if it doesn't have data for the selected model
                    imageResult.style.display = 'none';
                }
            }
        });
    }

    applySorting() {
        if (!this.currentImageData) return;

        // Re-render the content with new sorting
        const sortedImageFiles = this.sortImageFiles(this.currentImageData);

        let html = '';
        sortedImageFiles.forEach(imageResult => {
            html += this.renderImageResult(imageResult);
        });

        document.getElementById('details-content').innerHTML = html;

        // Re-apply current filters after sorting
        this.applyFilters();
    }

    // Toggle image result expansion with sticky header functionality
    toggleImageResult(header) {
        const content = header.nextElementSibling;
        const isExpanded = content.classList.contains('show');

        // Toggle the content visibility
        content.classList.toggle('show');
        header.classList.toggle('expanded');

        if (!isExpanded) {
            // Content is being expanded - set up sticky behavior
            this.setupStickyHeader(header);
        } else {
            // Content is being collapsed - remove sticky behavior
            this.removeStickyHeader(header);
        }
    }

    // Set up sticky header behavior for expanded image results
    setupStickyHeader(header) {
        // Add scroll listener to make header sticky when it reaches the top
        const scrollHandler = () => {
            const headerRect = header.getBoundingClientRect();
            const content = header.nextElementSibling;

            // Only apply sticky if the content is still expanded
            if (content.classList.contains('show')) {
                if (headerRect.top <= 0 && headerRect.bottom > 0) {
                    header.classList.add('sticky');
                } else {
                    header.classList.remove('sticky');
                }
            }
        };

        // Store the scroll handler on the header element for later removal
        header._scrollHandler = scrollHandler;
        window.addEventListener('scroll', scrollHandler);

        // Initial check
        scrollHandler();
    }

    // Remove sticky header behavior
    removeStickyHeader(header) {
        header.classList.remove('sticky');

        // Remove the scroll event listener
        if (header._scrollHandler) {
            window.removeEventListener('scroll', header._scrollHandler);
            delete header._scrollHandler;
        }
    }

    // Clean up all sticky headers when navigating away from details view
    cleanupStickyHeaders() {
        const stickyHeaders = document.querySelectorAll('.image-result-header.sticky');
        stickyHeaders.forEach(header => {
            this.removeStickyHeader(header);
        });
    }
}
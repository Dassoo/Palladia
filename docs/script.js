class BenchmarkDashboard {
    constructor() {
        this.data = {};
        this.init();
    }

    async init() {
        console.log('Starting to load data...');
        document.getElementById('overall-stats').innerHTML = '<div class="loading">Loading data...</div>';
        document.getElementById('model-averages').innerHTML = '<div class="loading">Loading data...</div>';
        document.getElementById('results-container').innerHTML = '<div class="loading">Loading data...</div>';

        try {
            await this.loadData();
            console.log('Data loaded successfully');
            this.renderOverallStats();
            this.renderModelAverages();
            this.renderResults();
        } catch (error) {
            console.error('Error loading data:', error);
            document.getElementById('overall-stats').innerHTML = `<div style="color: red; padding: 20px;">Error: ${error.message}</div>`;
            document.getElementById('model-averages').innerHTML = `<div style="color: red; padding: 20px;">Error: ${error.message}</div>`;
            document.getElementById('results-container').innerHTML = `<div style="color: red; padding: 20px;">Error: ${error.message}</div>`;
        }
    }

    async fetchWithTimeout(url, timeout = 5000) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);

        try {
            console.log(`Fetching: ${url}`);
            const response = await fetch(url, { signal: controller.signal });
            clearTimeout(timeoutId);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText} for ${url}`);
            }

            const data = await response.json();
            console.log(`Successfully loaded: ${url}`);
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
            // Load files with timeout
            const [data1, data2] = await Promise.all([
                this.fetchWithTimeout('json/GT4HistOCR/corpus/EarlyModernLatin/1471-Orthographia-Tortellius.json'),
                this.fetchWithTimeout('json/results/GT4HistOCR/corpus/EarlyModernLatin/1476-SpeculumNaturale-Beauvais.json'),
            ]);

            this.data = {
                'EarlyModernLatin': {
                    '1471-Orthographia-Tortellius': data1,
                    '1476-SpeculumNaturale-Beauvais': data2
                }
            };
        } catch (error) {
            throw new Error(`Failed to load benchmark data: ${error.message}`);
        }
    }

    calculateOverallStats() {
        const allResults = [];

        Object.values(this.data).forEach(category => {
            Object.values(category).forEach(subcategory => {
                Object.values(subcategory).forEach(modelData => {
                    allResults.push(modelData);
                });
            });
        });

        if (allResults.length === 0) return null;

        const totals = allResults.reduce((acc, result) => {
            acc.wer += result.avg_wer;
            acc.cer += result.avg_cer;
            acc.accuracy += result.avg_accuracy;
            acc.time += result.avg_time;
            acc.images += result.images;
            return acc;
        }, { wer: 0, cer: 0, accuracy: 0, time: 0, images: 0 });

        const count = allResults.length;
        return {
            avg_wer: (totals.wer / count).toFixed(2),
            avg_cer: (totals.cer / count).toFixed(2),
            avg_accuracy: (totals.accuracy / count).toFixed(2),
            avg_time: (totals.time / count).toFixed(2),
            total_images: totals.images,
            total_models: count
        };
    }

    renderOverallStats() {
        const stats = this.calculateOverallStats();
        if (!stats) return;

        const html = `
            <div class="stat-card">
                <div class="stat-label">Average Accuracy</div>
                <div class="stat-value">${stats.avg_accuracy}%</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Average CER</div>
                <div class="stat-value">${stats.avg_cer}%</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Average WER</div>
                <div class="stat-value">${stats.avg_wer}%</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Average Time</div>
                <div class="stat-value">${stats.avg_time}s</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Total Images</div>
                <div class="stat-value">${stats.total_images}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Evaluated Models</div>
                <div class="stat-value">${stats.total_models}</div>
            </div>
        `;

        document.getElementById('overall-stats').innerHTML = html;
    }

    calculateModelAverages() {
        const modelStats = {};

        // Collect all results for each model
        Object.values(this.data).forEach(category => {
            Object.values(category).forEach(subcategory => {
                Object.entries(subcategory).forEach(([modelName, modelData]) => {
                    if (!modelStats[modelName]) {
                        modelStats[modelName] = {
                            results: [],
                            totalImages: 0
                        };
                    }
                    modelStats[modelName].results.push(modelData);
                    modelStats[modelName].totalImages += modelData.images;
                });
            });
        });

        // Calculate averages for each model
        const modelAverages = {};
        Object.entries(modelStats).forEach(([modelName, stats]) => {
            const count = stats.results.length;
            const totals = stats.results.reduce((acc, result) => {
                acc.wer += result.avg_wer;
                acc.cer += result.avg_cer;
                acc.accuracy += result.avg_accuracy;
                acc.time += result.avg_time;
                return acc;
            }, { wer: 0, cer: 0, accuracy: 0, time: 0 });

            modelAverages[modelName] = {
                avg_wer: totals.wer / count,
                avg_cer: totals.cer / count,
                avg_accuracy: totals.accuracy / count,
                avg_time: totals.time / count,
                totalImages: stats.totalImages,
                benchmarkCount: count
            };
        });

        return modelAverages;
    }

    renderModelAverages() {
        const modelAverages = this.calculateModelAverages();
        if (!modelAverages || Object.keys(modelAverages).length === 0) return;

        // Sort models by accuracy (highest first)
        const sortedModels = Object.entries(modelAverages).sort(([, a], [, b]) => b.avg_accuracy - a.avg_accuracy);

        // Find best scores for highlighting
        const allModels = Object.values(modelAverages);
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
                        <th>Model</th>
                        <th>Accuracy (%)</th>
                        <th>CER (%)</th>
                        <th>WER (%)</th>
                        <th>Time (s)</th>
                        <th>Total Images</th>
                    </tr>
                </thead>
                <tbody>`;

        sortedModels.forEach(([modelName, modelData]) => {
            const werClass = modelData.avg_wer === best.wer ? 'best-score' : '';
            const cerClass = modelData.avg_cer === best.cer ? 'best-score' : '';
            const accClass = modelData.avg_accuracy === best.accuracy ? 'best-score' : '';
            const timeClass = modelData.avg_time === best.time ? 'best-score' : '';

            html += `
                <tr>
                    <td class="model-name">${modelName}</td>
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

                html += `
                    <div class="subcategory">
                        <div class="subcategory-header" onclick="this.nextElementSibling.classList.toggle('show'); this.classList.toggle('expanded')">
                            ${subcategoryName} (${Object.values(subcategoryData)[0].images} images)
                        </div>
                        <div class="model-results">
                            <table class="results-table">
                                <thead>
                                    <tr>
                                        <th>Model</th>
                                        <th>Accuracy (%)</th>
                                        <th>CER (%)</th>
                                        <th>WER (%)</th>
                                        <th>Time (s)</th>
                                    </tr>
                                </thead>
                                <tbody>`;

                // Sort models by accuracy (highest first)
                const sortedModels = Object.entries(subcategoryData).sort(([, a], [, b]) => b.avg_accuracy - a.avg_accuracy);

                sortedModels.forEach(([modelName, modelData]) => {
                    const werClass = modelData.avg_wer === best.wer ? 'best-score' : '';
                    const cerClass = modelData.avg_cer === best.cer ? 'best-score' : '';
                    const accClass = modelData.avg_accuracy === best.accuracy ? 'best-score' : '';
                    const timeClass = modelData.avg_time === best.time ? 'best-score' : '';

                    html += `
                        <tr>
                            <td class="model-name">${modelName}</td>
                            <td class="${accClass}">${modelData.avg_accuracy.toFixed(2)}</td>
                            <td class="${cerClass}">${modelData.avg_cer.toFixed(2)}</td>
                            <td class="${werClass}">${modelData.avg_wer.toFixed(2)}</td>
                            <td class="${timeClass}">${modelData.avg_time.toFixed(2)}</td>
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
    }
}

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', () => {
    new BenchmarkDashboard();
});
// Individual File Loader for loading detailed image results
class IndividualFileLoader {
    constructor(fetchFunction) {
        this.fetchWithTimeout = fetchFunction;
        this.cache = new Map();
    }

    async loadIndividualFiles(filePaths) {
        const results = {
            successful: [],
            failed: [],
            data: {}
        };

        const loadPromises = filePaths.map(async (filePath) => {
            try {
                // Check cache first
                if (this.cache.has(filePath)) {
                    return { filePath, data: this.cache.get(filePath), success: true, cached: true };
                }

                const data = await this.fetchWithTimeout(`data/json/${filePath}`);
                const processedData = this.processImageData(data, filePath);

                // Cache the processed data
                this.cache.set(filePath, processedData);

                return { filePath, data: processedData, success: true, cached: false };
            } catch (error) {
                console.warn(`Failed to load ${filePath}:`, error.message);
                return { filePath, error: error.message, success: false };
            }
        });

        const loadResults = await Promise.all(loadPromises);

        loadResults.forEach(result => {
            if (result.success) {
                results.successful.push(result);
                results.data[result.filePath] = result.data;
            } else {
                results.failed.push(result);
            }
        });

        return results;
    }

    processImageData(rawData, filePath) {
        // Extract filename for display
        const filename = filePath.split('/').pop().replace('.json', '');

        // Validate and normalize the data structure
        const processedData = {
            filename: filename,
            filePath: filePath,
            models: {}
        };

        // Process each model's data
        Object.entries(rawData).forEach(([modelName, modelData]) => {
            if (this.validateModelData(modelData)) {
                processedData.models[modelName] = {
                    groundTruth: modelData.gt || '',
                    response: modelData.response || '',
                    wer: modelData.wer || 0,
                    cer: modelData.cer || 0,
                    accuracy: modelData.accuracy || 0,
                    time: modelData.time || 0
                };
            } else {
                console.warn(`Invalid data structure for model ${modelName} in ${filePath}`);
            }
        });

        return processedData;
    }

    validateModelData(modelData) {
        const requiredKeys = ['gt', 'response', 'wer', 'cer', 'accuracy', 'time'];
        return typeof modelData === 'object' &&
            modelData !== null &&
            requiredKeys.every(key => key in modelData);
    }

    handleLoadingErrors(errors) {
        if (errors.length === 0) return;
        console.error(`Failed to load ${errors.length} files:`, errors);
    }
}
// Simple Diff Viewer for text comparison
class DiffViewer {
    static generateDiff(text1, text2) {
        // Simple word-based diff implementation
        const words1 = text1.split(/(\s+)/);
        const words2 = text2.split(/(\s+)/);

        const diff = [];
        let i = 0, j = 0;

        while (i < words1.length || j < words2.length) {
            if (i >= words1.length) {
                // Remaining words in text2 are additions
                diff.push({ type: 'added', value: words2[j] });
                j++;
            } else if (j >= words2.length) {
                // Remaining words in text1 are deletions
                diff.push({ type: 'removed', value: words1[i] });
                i++;
            } else if (words1[i] === words2[j]) {
                // Words match
                diff.push({ type: 'equal', value: words1[i] });
                i++;
                j++;
            } else {
                // Words differ - simple approach: mark as changed
                diff.push({ type: 'removed', value: words1[i] });
                diff.push({ type: 'added', value: words2[j] });
                i++;
                j++;
            }
        }

        return diff;
    }

    static renderInlineDiff(diff) {
        return diff.map(part => {
            const className = part.type === 'added' ? 'diff-added' :
                part.type === 'removed' ? 'diff-removed' : '';
            return className ?
                `<span class="${className}">${this.escapeHtml(part.value)}</span>` :
                this.escapeHtml(part.value);
        }).join('');
    }

    static escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}
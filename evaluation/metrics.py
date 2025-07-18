from diff_match_patch import diff_match_patch
from jiwer import wer, cer
from bert_score import score
from rich.text import Text

def get_diff(candidate: str, reference: str):
    """Get the differences between the candidate and reference strings."""
    dmp = diff_match_patch()
    diffs = dmp.diff_main(reference, candidate)
    
    # Count matches, deletions, and insertions
    match_count = sum(len(text) for op, text in diffs if op == 0)
    deletion_count = sum(len(text) for op, text in diffs if op == -1)  # missing from candidate
    insertion_count = sum(len(text) for op, text in diffs if op == 1)   # extra in candidate
    
    # Calculate accuracy considering all operations
    # Total possible operations = length of the longer string + insertions
    total_operations = max(len(reference), len(candidate))
    if total_operations == 0:
        accuracy = 1.0
    else:
        # Accuracy = correct characters / total characters in alignment
        accuracy = match_count / total_operations
    
    text = Text()
    for op, data in diffs:
        if op == 0:
            text.append(data, style="green")
        elif op == -1:
            text.append(data, style="bold yellow")  # missing from candidate
        elif op == 1:
            text.append(data, style="bold red")  # extra in candidate
    
    return text, accuracy

def get_metrics(candidate: str, reference: str):
    """Get the word error rate and character error rate between the candidate and reference strings."""
    w_error = wer(candidate, reference)
    c_error = cer(candidate, reference)
    return w_error, c_error

def get_bert_score(candidate: str, reference: str):
    """Get the BERT score between the candidate and reference strings."""
    P, R, F1 = score([candidate], [reference], lang="en", verbose=True)
    return P, R, F1
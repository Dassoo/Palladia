from diff_match_patch import diff_match_patch
from jiwer import wer, cer
from bert_score import score
from rich.text import Text

def get_diff(candidate: str, reference: str):
    """Get the differences between the candidate and reference strings."""
    dmp = diff_match_patch()
    diffs = dmp.diff_main(reference, candidate)
    
    match_count = sum(len(text) for op, text in diffs if op == 0)
    total_length = max(len(reference), 1)
    accuracy = match_count / total_length
    
    text = Text()
    for op, data in diffs:
        if op == 0:
            text.append(data, style="green")
        elif op == -1:
            text.append(data, style="bold yellow")  # extra
        elif op == 1:
            text.append(data, style="bold red")  # missing
    
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
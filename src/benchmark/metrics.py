from diff_match_patch import diff_match_patch
from jiwer import wer, cer


def get_diff(candidate: str, reference: str):
    """Get character-level differences and an accuracy score."""
    dmp = diff_match_patch()
    diffs = dmp.diff_main(reference, candidate)
    dmp.diff_cleanupSemantic(diffs)

    match_count = sum(len(text) for op, text in diffs if op == 0)
    deletion_count = sum(len(text) for op, text in diffs if op == -1)
    insertion_count = sum(len(text) for op, text in diffs if op == 1)

    total = max(len(reference), len(candidate))
    accuracy = match_count / total if total > 0 else 1.0

    return {
        "diffs": diffs,  # list of (op, text)
        "matches": match_count,
        "deletions": deletion_count,
        "insertions": insertion_count,
        "accuracy": accuracy,
    }


def get_metrics(candidate: str, reference: str):
    """Get word error rate and character error rate."""
    w_error = min(wer(reference, candidate), 1.0)
    c_error = min(cer(reference, candidate), 1.0)
    return w_error, c_error

def escapeseq(value):
    """
    An "escape" filter for sequences. Mark each element in the sequence,
    individually, as a string that should be auto-escaped. Return a list with
    the results.
    """
    return [conditional_escape(obj) for obj in value]
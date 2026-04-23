def _check_chunk_size(reduced, chunk_size):
    """Checks chunk is a sequence of expected size or a tuple of same."""
    if reduced is None:
        return
    is_tuple = isinstance(reduced, tuple)
    if not is_tuple:
        reduced = (reduced,)
    if any(isinstance(r, tuple) or not hasattr(r, "__iter__") for r in reduced):
        raise TypeError(
            "reduce_func returned %r. Expected sequence(s) of length %d."
            % (reduced if is_tuple else reduced[0], chunk_size)
        )
    if any(_num_samples(r) != chunk_size for r in reduced):
        actual_size = tuple(_num_samples(r) for r in reduced)
        raise ValueError(
            "reduce_func returned object of length %s. "
            "Expected same length as input: %d."
            % (actual_size if is_tuple else actual_size[0], chunk_size)
        )
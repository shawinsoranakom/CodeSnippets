def _cosine_similarity(x: Matrix, y: Matrix) -> np.ndarray:
    """Row-wise cosine similarity between two equal-width matrices.

    Args:
        x: A matrix of shape `(n, m)`.
        y: A matrix of shape `(k, m)`.

    Returns:
        A matrix of shape `(n, k)` where each element `(i, j)` is the cosine similarity
            between the `i`th row of `x` and the `j`th row of `y`.

    Raises:
        ValueError: If the number of columns in `x` and `y` are not the same.
        ImportError: If numpy is not installed.
    """
    if not _HAS_NUMPY:
        msg = (
            "cosine_similarity requires numpy to be installed. "
            "Please install numpy with `pip install numpy`."
        )
        raise ImportError(msg)

    if len(x) == 0 or len(y) == 0:
        return np.array([[]])

    x = np.array(x)
    y = np.array(y)

    # Check for NaN
    if np.any(np.isnan(x)) or np.any(np.isnan(y)):
        warnings.warn(
            "NaN found in input arrays, unexpected return might follow",
            category=RuntimeWarning,
            stacklevel=2,
        )

    # Check for Inf
    if np.any(np.isinf(x)) or np.any(np.isinf(y)):
        warnings.warn(
            "Inf found in input arrays, unexpected return might follow",
            category=RuntimeWarning,
            stacklevel=2,
        )

    if x.shape[1] != y.shape[1]:
        msg = (
            f"Number of columns in X and Y must be the same. X has shape {x.shape} "
            f"and Y has shape {y.shape}."
        )
        raise ValueError(msg)
    if not _HAS_SIMSIMD:
        logger.debug(
            "Unable to import simsimd, defaulting to NumPy implementation. If you want "
            "to use simsimd please install with `pip install simsimd`."
        )
        x_norm = np.linalg.norm(x, axis=1)
        y_norm = np.linalg.norm(y, axis=1)
        # Ignore divide by zero errors run time warnings as those are handled below.
        with np.errstate(divide="ignore", invalid="ignore"):
            similarity = np.dot(x, y.T) / np.outer(x_norm, y_norm)
        if np.isnan(similarity).all():
            msg = "NaN values found, please remove the NaN values and try again"
            raise ValueError(msg) from None
        similarity[np.isnan(similarity) | np.isinf(similarity)] = 0.0
        return cast("np.ndarray", similarity)

    x = np.array(x, dtype=np.float32)
    y = np.array(y, dtype=np.float32)
    return 1 - np.array(simd.cdist(x, y, metric="cosine"))
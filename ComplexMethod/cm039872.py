def resample(
    *arrays,
    replace=True,
    n_samples=None,
    random_state=None,
    stratify=None,
    sample_weight=None,
):
    """Resample arrays or sparse matrices in a consistent way.

    The default strategy implements one step of the bootstrapping
    procedure.

    Parameters
    ----------
    *arrays : sequence of array-like of shape (n_samples,) or \
            (n_samples, n_outputs)
        Indexable data-structures can be arrays, lists, dataframes or scipy
        sparse matrices with consistent first dimension.

    replace : bool, default=True
        Implements resampling with replacement. It must be set to True
        whenever sampling with non-uniform weights: a few data points with very large
        weights are expected to be sampled several times with probability to preserve
        the distribution induced by the weights. If False, this will implement
        (sliced) random permutations.

    n_samples : int, default=None
        Number of samples to generate. If left to None this is
        automatically set to the first dimension of the arrays.
        If replace is False it should not be larger than the length of
        arrays.

    random_state : int, RandomState instance or None, default=None
        Determines random number generation for shuffling
        the data.
        Pass an int for reproducible results across multiple function calls.
        See :term:`Glossary <random_state>`.

    stratify : {array-like, sparse matrix} of shape (n_samples,) or \
            (n_samples, n_outputs), default=None
        If not None, data is split in a stratified fashion, using this as
        the class labels.

    sample_weight : array-like of shape (n_samples,), default=None
        Contains weight values to be associated with each sample. Values are
        normalized to sum to one and interpreted as probability for sampling
        each data point.

        .. versionadded:: 1.7

    Returns
    -------
    resampled_arrays : sequence of array-like of shape (n_samples,) or \
            (n_samples, n_outputs)
        Sequence of resampled copies of the collections. The original arrays
        are not impacted.

    See Also
    --------
    shuffle : Shuffle arrays or sparse matrices in a consistent way.

    Examples
    --------
    It is possible to mix sparse and dense arrays in the same run::

      >>> import numpy as np
      >>> X = np.array([[1., 0.], [2., 1.], [0., 0.]])
      >>> y = np.array([0, 1, 2])

      >>> from scipy.sparse import coo_array
      >>> X_sparse = coo_array(X)

      >>> from sklearn.utils import resample
      >>> X, X_sparse, y = resample(X, X_sparse, y, random_state=0)
      >>> X
      array([[1., 0.],
             [2., 1.],
             [1., 0.]])

      >>> X_sparse
      <Compressed Sparse Row sparse array of dtype 'float64'
          with 4 stored elements and shape (3, 2)>

      >>> X_sparse.toarray()
      array([[1., 0.],
             [2., 1.],
             [1., 0.]])

      >>> y
      array([0, 1, 0])

      >>> resample(y, n_samples=2, random_state=0)
      array([0, 1])

    Example using stratification::

      >>> y = [0, 0, 1, 1, 1, 1, 1, 1, 1]
      >>> resample(y, n_samples=5, replace=False, stratify=y,
      ...          random_state=0)
      [1, 1, 1, 0, 1]
    """
    max_n_samples = n_samples
    random_state = check_random_state(random_state)

    if len(arrays) == 0:
        return None

    first = arrays[0]
    n_samples = first.shape[0] if hasattr(first, "shape") else len(first)

    if max_n_samples is None:
        max_n_samples = n_samples
    elif (max_n_samples > n_samples) and (not replace):
        raise ValueError(
            "Cannot sample %d out of arrays with dim %d when replace is False"
            % (max_n_samples, n_samples)
        )

    check_consistent_length(*arrays)

    if sample_weight is not None and not replace:
        raise NotImplementedError(
            "Resampling with sample_weight is only implemented for replace=True."
        )
    if sample_weight is not None and stratify is not None:
        raise NotImplementedError(
            "Resampling with sample_weight is only implemented for stratify=None."
        )
    if stratify is None:
        if replace:
            if sample_weight is not None:
                sample_weight = _check_sample_weight(
                    sample_weight, first, dtype=np.float64
                )
                p = sample_weight / sample_weight.sum()
            else:
                p = None
            indices = random_state.choice(
                n_samples,
                size=max_n_samples,
                p=p,
                replace=True,
            )
        else:
            indices = np.arange(n_samples)
            random_state.shuffle(indices)
            indices = indices[:max_n_samples]
    else:
        # Code adapted from StratifiedShuffleSplit()
        y = check_array(stratify, ensure_2d=False, dtype=None)
        if y.ndim == 2:
            # for multi-label y, map each distinct row to a string repr
            # using join because str(row) uses an ellipsis if len(row) > 1000
            y = np.array([" ".join(row.astype("str")) for row in y])

        classes, y_indices = np.unique(y, return_inverse=True)
        n_classes = classes.shape[0]

        class_counts = np.bincount(y_indices)

        # Find the sorted list of instances for each class:
        # (np.unique above performs a sort, so code is O(n logn) already)
        class_indices = np.split(
            np.argsort(y_indices, kind="mergesort"), np.cumsum(class_counts)[:-1]
        )

        n_i = _approximate_mode(class_counts, max_n_samples, random_state)

        indices = []

        for i in range(n_classes):
            indices_i = random_state.choice(class_indices[i], n_i[i], replace=replace)
            indices.extend(indices_i)

        indices = random_state.permutation(indices)

    # convert sparse matrices to CSR for row-based indexing
    arrays = [a.tocsr() if issparse(a) else a for a in arrays]
    resampled_arrays = [_safe_indexing(a, indices) for a in arrays]
    if len(resampled_arrays) == 1:
        # syntactic sugar for the unit argument case
        return resampled_arrays[0]
    else:
        return resampled_arrays
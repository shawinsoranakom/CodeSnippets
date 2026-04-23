def class_distribution(y, sample_weight=None):
    """Compute class priors from multioutput-multiclass target data.

    Parameters
    ----------
    y : {array-like, sparse matrix} of size (n_samples, n_outputs)
        The labels for each example.

    sample_weight : array-like of shape (n_samples,), default=None
        Sample weights.

    Returns
    -------
    classes : list of size n_outputs of ndarray of size (n_classes,)
        List of classes for each column.

    n_classes : list of int of size n_outputs
        Number of classes in each column.

    class_prior : list of size n_outputs of ndarray of size (n_classes,)
        Class distribution of each column.
    """
    classes = []
    n_classes = []
    class_prior = []

    n_samples, n_outputs = y.shape
    if sample_weight is not None:
        sample_weight = np.asarray(sample_weight)

    if issparse(y):
        y = y.tocsc()
        y_nnz = np.diff(y.indptr)

        for k in range(n_outputs):
            col_nonzero = y.indices[y.indptr[k] : y.indptr[k + 1]]
            # separate sample weights for zero and non-zero elements
            if sample_weight is not None:
                nz_samp_weight = sample_weight[col_nonzero]
                zeros_samp_weight_sum = np.sum(sample_weight) - np.sum(nz_samp_weight)
            else:
                nz_samp_weight = None
                zeros_samp_weight_sum = y.shape[0] - y_nnz[k]

            classes_k, y_k = np.unique(
                y.data[y.indptr[k] : y.indptr[k + 1]], return_inverse=True
            )
            class_prior_k = np.bincount(y_k, weights=nz_samp_weight)

            # An explicit zero was found, combine its weight with the weight
            # of the implicit zeros
            if 0 in classes_k:
                class_prior_k[classes_k == 0] += zeros_samp_weight_sum

            # If there is an implicit zero and it is not in classes and
            # class_prior, make an entry for it
            if 0 not in classes_k and y_nnz[k] < y.shape[0]:
                classes_k = np.insert(classes_k, 0, 0)
                class_prior_k = np.insert(class_prior_k, 0, zeros_samp_weight_sum)

            classes.append(classes_k)
            n_classes.append(classes_k.shape[0])
            class_prior.append(class_prior_k / class_prior_k.sum())
    else:
        for k in range(n_outputs):
            classes_k, y_k = np.unique(y[:, k], return_inverse=True)
            classes.append(classes_k)
            n_classes.append(classes_k.shape[0])
            class_prior_k = np.bincount(y_k, weights=sample_weight)
            class_prior.append(class_prior_k / class_prior_k.sum())

    return (classes, n_classes, class_prior)
def inverse_transform(self, Y, threshold=None):
        """Transform binary labels back to multi-class labels.

        Parameters
        ----------
        Y : {ndarray, sparse matrix} of shape (n_samples, n_classes)
            Target values. All sparse matrices are converted to CSR before
            inverse transformation.

        threshold : float, default=None
            Threshold used in the binary and multi-label cases.

            Use 0 when ``Y`` contains the output of :term:`decision_function`
            (classifier).
            Use 0.5 when ``Y`` contains the output of :term:`predict_proba`.

            If None, the threshold is assumed to be half way between
            neg_label and pos_label.

        Returns
        -------
        y_original : {ndarray, sparse matrix} of shape (n_samples,)
            Target values. Sparse matrix will be of CSR format.

        Notes
        -----
        In the case when the binary labels are fractional
        (probabilistic), :meth:`inverse_transform` chooses the class with the
        greatest value. Typically, this allows to use the output of a
        linear model's :term:`decision_function` method directly as the input
        of :meth:`inverse_transform`.
        """
        check_is_fitted(self)

        xp, is_array_api = get_namespace(Y)

        if is_array_api and self.sparse_input_ and not _is_numpy_namespace(xp):
            raise ValueError(
                "`LabelBinarizer` was fitted on a sparse matrix, and therefore cannot "
                f"inverse transform a {xp.__name__} array back to a sparse matrix."
            )

        if threshold is None:
            threshold = (self.pos_label + self.neg_label) / 2.0

        if self.y_type_ == "multiclass":
            y_inv = _inverse_binarize_multiclass(Y, self.classes_, xp=xp)
        else:
            y_inv = _inverse_binarize_thresholding(
                Y, self.y_type_, self.classes_, threshold, xp=xp
            )

        if self.sparse_input_:
            y_inv = _align_api_if_sparse(sp.csr_array(y_inv))
        elif sp.issparse(y_inv):
            y_inv = y_inv.toarray()

        return y_inv
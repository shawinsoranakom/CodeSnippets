def fit(self, y):
        """Fit label binarizer.

        Parameters
        ----------
        y : ndarray of shape (n_samples,) or (n_samples, n_classes)
            Target values. The 2-d matrix should only contain 0 and 1,
            represents multilabel classification.

        Returns
        -------
        self : object
            Returns the instance itself.
        """
        if self.neg_label >= self.pos_label:
            raise ValueError(
                f"neg_label={self.neg_label} must be strictly less than "
                f"pos_label={self.pos_label}."
            )

        if self.sparse_output and (self.pos_label == 0 or self.neg_label != 0):
            raise ValueError(
                "Sparse binarization is only supported with non "
                "zero pos_label and zero neg_label, got "
                f"pos_label={self.pos_label} and neg_label={self.neg_label}"
            )

        xp, is_array_api = get_namespace(y)

        if is_array_api and self.sparse_output and not _is_numpy_namespace(xp):
            raise ValueError(
                "`sparse_output=True` is not supported for array API "
                f"namespace {xp.__name__}. "
                "Use `sparse_output=False` to return a dense array instead."
            )

        self.y_type_ = type_of_target(y, input_name="y")

        if "multioutput" in self.y_type_:
            raise ValueError(
                "Multioutput target data is not supported with label binarization"
            )
        if _num_samples(y) == 0:
            raise ValueError("y has 0 samples: %r" % y)

        self.sparse_input_ = sp.issparse(y)
        self.classes_ = unique_labels(y)
        return self
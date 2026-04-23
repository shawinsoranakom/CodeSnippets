def fit(self, X, y):
        """Fit the radius neighbors classifier from the training dataset.

        Parameters
        ----------
        X : {array-like, sparse matrix} of shape (n_samples, n_features) or \
                (n_samples, n_samples) if metric='precomputed'
            Training data.

        y : {array-like, sparse matrix} of shape (n_samples,) or \
                (n_samples, n_outputs)
            Target values.

        Returns
        -------
        self : RadiusNeighborsClassifier
            The fitted radius neighbors classifier.
        """
        self._fit(X, y)

        classes_ = self.classes_
        _y = self._y
        if not self.outputs_2d_:
            _y = self._y.reshape((-1, 1))
            classes_ = [self.classes_]

        if self.outlier_label is None:
            outlier_label_ = None

        elif self.outlier_label == "most_frequent":
            outlier_label_ = []
            # iterate over multi-output, get the most frequent label for each
            # output.
            for k, classes_k in enumerate(classes_):
                label_count = np.bincount(_y[:, k])
                outlier_label_.append(classes_k[label_count.argmax()])

        else:
            if _is_arraylike(self.outlier_label) and not isinstance(
                self.outlier_label, str
            ):
                if len(self.outlier_label) != len(classes_):
                    raise ValueError(
                        "The length of outlier_label: {} is "
                        "inconsistent with the output "
                        "length: {}".format(self.outlier_label, len(classes_))
                    )
                outlier_label_ = self.outlier_label
            else:
                outlier_label_ = [self.outlier_label] * len(classes_)

            for classes, label in zip(classes_, outlier_label_):
                if _is_arraylike(label) and not isinstance(label, str):
                    # ensure the outlier label for each output is a scalar.
                    raise TypeError(
                        "The outlier_label of classes {} is "
                        "supposed to be a scalar, got "
                        "{}.".format(classes, label)
                    )
                if np.append(classes, label).dtype != classes.dtype:
                    # ensure the dtype of outlier label is consistent with y.
                    raise TypeError(
                        "The dtype of outlier_label {} is "
                        "inconsistent with classes {} in "
                        "y.".format(label, classes)
                    )

        self.outlier_label_ = outlier_label_

        return self
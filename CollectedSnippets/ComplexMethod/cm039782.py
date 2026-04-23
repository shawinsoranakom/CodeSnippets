def fit(self, X, y):
        """Fit a semi-supervised label propagation model to X.

        The input samples (labeled and unlabeled) are provided by matrix X,
        and target labels are provided by matrix y. We conventionally apply the
        label -1 to unlabeled samples in matrix y in a semi-supervised
        classification.

        Parameters
        ----------
        X : {array-like, sparse matrix} of shape (n_samples, n_features)
            Training data, where `n_samples` is the number of samples
            and `n_features` is the number of features.

        y : array-like of shape (n_samples,)
            Target class values with unlabeled points marked as -1.
            All unlabeled samples will be transductively assigned labels
            internally, which are stored in `transduction_`.

        Returns
        -------
        self : object
            Returns the instance itself.
        """
        X, y = validate_data(
            self,
            X,
            y,
            accept_sparse=["csr", "csc"],
            reset=True,
        )
        self.X_ = X
        check_classification_targets(y)

        # actual graph construction (implementations should override this)
        graph_matrix = self._build_graph()

        # label construction
        # construct a categorical distribution for classification only
        classes = np.unique(y)
        classes = classes[classes != -1]
        self.classes_ = classes

        n_samples, n_classes = len(y), len(classes)

        y = np.asarray(y)
        unlabeled = y == -1

        # initialize distributions
        self.label_distributions_ = np.zeros((n_samples, n_classes))
        for label in classes:
            self.label_distributions_[y == label, classes == label] = 1

        y_static = np.copy(self.label_distributions_)
        if self._variant == "propagation":
            # LabelPropagation
            y_static[unlabeled] = 0
        else:
            # LabelSpreading
            y_static *= 1 - self.alpha

        l_previous = np.zeros((self.X_.shape[0], n_classes))

        unlabeled = unlabeled[:, np.newaxis]
        if sparse.issparse(graph_matrix):
            graph_matrix = graph_matrix.tocsr()

        for self.n_iter_ in range(self.max_iter):
            if np.abs(self.label_distributions_ - l_previous).sum() < self.tol:
                break

            l_previous = self.label_distributions_
            self.label_distributions_ = safe_sparse_dot(
                graph_matrix, self.label_distributions_
            )

            if self._variant == "propagation":
                normalizer = np.sum(self.label_distributions_, axis=1)[:, np.newaxis]
                normalizer[normalizer == 0] = 1
                self.label_distributions_ /= normalizer
                self.label_distributions_ = np.where(
                    unlabeled, self.label_distributions_, y_static
                )
            else:
                # clamp
                self.label_distributions_ = (
                    np.multiply(self.alpha, self.label_distributions_) + y_static
                )
        else:
            warnings.warn(
                "max_iter=%d was reached without convergence." % self.max_iter,
                category=ConvergenceWarning,
            )
            self.n_iter_ += 1

        normalizer = np.sum(self.label_distributions_, axis=1)[:, np.newaxis]
        normalizer[normalizer == 0] = 1
        self.label_distributions_ /= normalizer

        # set the transduction item
        transduction = self.classes_[np.argmax(self.label_distributions_, axis=1)]
        self.transduction_ = transduction.ravel()
        return self
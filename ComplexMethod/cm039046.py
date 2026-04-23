def predict_proba(self, X):
        """
        Return probability estimates for the test vectors X.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Test data.

        Returns
        -------
        P : ndarray of shape (n_samples, n_classes) or list of such arrays
            Returns the probability of the sample for each class in
            the model, where classes are ordered arithmetically, for each
            output.
        """
        check_is_fitted(self)

        # numpy random_state expects Python int and not long as size argument
        # under Windows
        n_samples = _num_samples(X)
        rs = check_random_state(self.random_state)

        n_classes_ = self.n_classes_
        classes_ = self.classes_
        class_prior_ = self.class_prior_
        constant = self.constant
        if self.n_outputs_ == 1:
            # Get same type even for self.n_outputs_ == 1
            n_classes_ = [n_classes_]
            classes_ = [classes_]
            class_prior_ = [class_prior_]
            constant = [constant]

        P = []
        for k in range(self.n_outputs_):
            if self._strategy == "most_frequent":
                ind = class_prior_[k].argmax()
                out = np.zeros((n_samples, n_classes_[k]), dtype=np.float64)
                out[:, ind] = 1.0
            elif self._strategy == "prior":
                out = np.ones((n_samples, 1)) * class_prior_[k]

            elif self._strategy == "stratified":
                out = rs.multinomial(1, class_prior_[k], size=n_samples)
                out = out.astype(np.float64)

            elif self._strategy == "uniform":
                out = np.ones((n_samples, n_classes_[k]), dtype=np.float64)
                out /= n_classes_[k]

            elif self._strategy == "constant":
                ind = np.where(classes_[k] == constant[k])
                out = np.zeros((n_samples, n_classes_[k]), dtype=np.float64)
                out[:, ind] = 1.0

            P.append(out)

        if self.n_outputs_ == 1:
            P = P[0]

        return P
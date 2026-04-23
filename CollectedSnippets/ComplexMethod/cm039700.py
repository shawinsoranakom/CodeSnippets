def fit(
        self,
        X,
        Y=None,
        sample_weight=None,
        class_prior=None,
        sparse_sample_weight=None,
        sparse_param=None,
        dummy_int=None,
        dummy_str=None,
        dummy_obj=None,
        callback=None,
    ):
        """The dummy arguments are to test that this fit function can
        accept non-array arguments through cross-validation, such as:
            - int
            - str (this is actually array-like)
            - object
            - function
        """
        self.dummy_int = dummy_int
        self.dummy_str = dummy_str
        self.dummy_obj = dummy_obj
        if callback is not None:
            callback(self)

        if self.allow_nd:
            X = X.reshape(len(X), -1)
        if X.ndim >= 3 and not self.allow_nd:
            raise ValueError("X cannot be d")
        if sample_weight is not None:
            assert sample_weight.shape[0] == X.shape[0], (
                "MockClassifier extra fit_param "
                "sample_weight.shape[0] is {0}, should be {1}".format(
                    sample_weight.shape[0], X.shape[0]
                )
            )
        if class_prior is not None:
            assert class_prior.shape[0] == len(np.unique(y)), (
                "MockClassifier extra fit_param class_prior.shape[0]"
                " is {0}, should be {1}".format(class_prior.shape[0], len(np.unique(y)))
            )
        if sparse_sample_weight is not None:
            fmt = (
                "MockClassifier extra fit_param sparse_sample_weight"
                ".shape[0] is {0}, should be {1}"
            )
            assert sparse_sample_weight.shape[0] == X.shape[0], fmt.format(
                sparse_sample_weight.shape[0], X.shape[0]
            )
        if sparse_param is not None:
            fmt = (
                "MockClassifier extra fit_param sparse_param.shape "
                "is ({0}, {1}), should be ({2}, {3})"
            )
            assert sparse_param.shape == P.shape, fmt.format(
                sparse_param.shape[0],
                sparse_param.shape[1],
                P.shape[0],
                P.shape[1],
            )
        self.classes_ = np.unique(y)
        return self
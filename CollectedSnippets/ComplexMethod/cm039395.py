def _initialize(self, X, y, init):
        """Initialize the transformation.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            The training samples.

        y : array-like of shape (n_samples,)
            The training labels.

        init : str or ndarray of shape (n_features_a, n_features_b)
            The validated initialization of the linear transformation.

        Returns
        -------
        transformation : ndarray of shape (n_components, n_features)
            The initialized linear transformation.

        """

        transformation = init
        if self.warm_start and hasattr(self, "components_"):
            transformation = self.components_
        elif isinstance(init, np.ndarray):
            pass
        else:
            n_samples, n_features = X.shape
            n_components = self.n_components or n_features
            if init == "auto":
                n_classes = len(np.unique(y))
                if n_components <= min(n_features, n_classes - 1):
                    init = "lda"
                elif n_components < min(n_features, n_samples):
                    init = "pca"
                else:
                    init = "identity"
            if init == "identity":
                transformation = np.eye(n_components, X.shape[1])
            elif init == "random":
                transformation = self.random_state_.standard_normal(
                    size=(n_components, X.shape[1])
                )
            elif init in {"pca", "lda"}:
                init_time = time.time()
                if init == "pca":
                    pca = PCA(
                        n_components=n_components, random_state=self.random_state_
                    )
                    if self.verbose:
                        print("Finding principal components... ", end="")
                        sys.stdout.flush()
                    pca.fit(X)
                    transformation = pca.components_
                elif init == "lda":
                    from sklearn.discriminant_analysis import LinearDiscriminantAnalysis

                    lda = LinearDiscriminantAnalysis(n_components=n_components)
                    if self.verbose:
                        print("Finding most discriminative components... ", end="")
                        sys.stdout.flush()
                    lda.fit(X, y)
                    transformation = lda.scalings_.T[:n_components]
                if self.verbose:
                    print("done in {:5.2f}s".format(time.time() - init_time))
        return transformation
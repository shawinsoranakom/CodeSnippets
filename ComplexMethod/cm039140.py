def _fit_transform_in_place(self, K):
        """Fit's using kernel K"""
        # center kernel in place
        K = self._centerer.fit(K).transform(K, copy=False)

        # adjust n_components according to user inputs
        if self.n_components is None:
            n_components = K.shape[0]  # use all dimensions
        else:
            n_components = min(K.shape[0], self.n_components)

        # compute eigenvectors
        if self.eigen_solver == "auto":
            if K.shape[0] > 200 and n_components < 10:
                eigen_solver = "arpack"
            else:
                eigen_solver = "dense"
        else:
            eigen_solver = self.eigen_solver

        if eigen_solver == "dense":
            # Note: subset_by_index specifies the indices of smallest/largest to return
            self.eigenvalues_, self.eigenvectors_ = eigh(
                K, subset_by_index=(K.shape[0] - n_components, K.shape[0] - 1)
            )
        elif eigen_solver == "arpack":
            v0 = _init_arpack_v0(K.shape[0], self.random_state)
            self.eigenvalues_, self.eigenvectors_ = eigsh(
                K, n_components, which="LA", tol=self.tol, maxiter=self.max_iter, v0=v0
            )
        elif eigen_solver == "randomized":
            self.eigenvalues_, self.eigenvectors_ = _randomized_eigsh(
                K,
                n_components=n_components,
                n_iter=self.iterated_power,
                random_state=self.random_state,
                selection="module",
            )

        # make sure that the eigenvalues are ok and fix numerical issues
        self.eigenvalues_ = _check_psd_eigenvalues(
            self.eigenvalues_, enable_warnings=False
        )

        # flip eigenvectors' sign to enforce deterministic output
        self.eigenvectors_, _ = svd_flip(u=self.eigenvectors_, v=None)

        # sort eigenvectors in descending order
        indices = self.eigenvalues_.argsort()[::-1]
        self.eigenvalues_ = self.eigenvalues_[indices]
        self.eigenvectors_ = self.eigenvectors_[:, indices]

        # remove eigenvectors with a zero eigenvalue (null space) if required
        if self.remove_zero_eig or self.n_components is None:
            self.eigenvectors_ = self.eigenvectors_[:, self.eigenvalues_ > 0]
            self.eigenvalues_ = self.eigenvalues_[self.eigenvalues_ > 0]

        # Maintenance note on Eigenvectors normalization
        # ----------------------------------------------
        # there is a link between
        # the eigenvectors of K=Phi(X)'Phi(X) and the ones of Phi(X)Phi(X)'
        # if v is an eigenvector of K
        #     then Phi(X)v  is an eigenvector of Phi(X)Phi(X)'
        # if u is an eigenvector of Phi(X)Phi(X)'
        #     then Phi(X)'u is an eigenvector of Phi(X)'Phi(X)
        #
        # At this stage our self.eigenvectors_ (the v) have norm 1, we need to scale
        # them so that eigenvectors in kernel feature space (the u) have norm=1
        # instead
        #
        # We COULD scale them here:
        #       self.eigenvectors_ = self.eigenvectors_ / np.sqrt(self.eigenvalues_)
        #
        # But choose to perform that LATER when needed, in `fit()` and in
        # `transform()`.

        return K
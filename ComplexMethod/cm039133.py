def fit(self, X, y=None):
        """Learn model for the data X with variational Bayes method.

        When `learning_method` is 'online', use mini-batch update.
        Otherwise, use batch update.

        Parameters
        ----------
        X : {array-like, sparse matrix} of shape (n_samples, n_features)
            Document word matrix.

        y : Ignored
            Not used, present here for API consistency by convention.

        Returns
        -------
        self
            Fitted estimator.
        """
        X = self._check_non_neg_array(
            X, reset_n_features=True, whom="LatentDirichletAllocation.fit"
        )
        n_samples, n_features = X.shape
        max_iter = self.max_iter
        evaluate_every = self.evaluate_every
        learning_method = self.learning_method

        batch_size = self.batch_size

        # initialize parameters
        self._init_latent_vars(n_features, dtype=X.dtype)
        # change to perplexity later
        last_bound = None
        n_jobs = effective_n_jobs(self.n_jobs)
        with Parallel(n_jobs=n_jobs, verbose=max(0, self.verbose - 1)) as parallel:
            for i in range(max_iter):
                if learning_method == "online":
                    for idx_slice in gen_batches(n_samples, batch_size):
                        self._em_step(
                            X[idx_slice, :],
                            total_samples=n_samples,
                            batch_update=False,
                            parallel=parallel,
                        )
                else:
                    # batch update
                    self._em_step(
                        X, total_samples=n_samples, batch_update=True, parallel=parallel
                    )

                # check perplexity
                if evaluate_every > 0 and (i + 1) % evaluate_every == 0:
                    doc_topics_distr, _ = self._e_step(
                        X, cal_sstats=False, random_init=False, parallel=parallel
                    )
                    bound = self._perplexity_precomp_distr(
                        X, doc_topics_distr, sub_sampling=False
                    )
                    if self.verbose:
                        print(
                            "iteration: %d of max_iter: %d, perplexity: %.4f"
                            % (i + 1, max_iter, bound)
                        )

                    if last_bound and abs(last_bound - bound) < self.perp_tol:
                        break
                    last_bound = bound

                elif self.verbose:
                    print("iteration: %d of max_iter: %d" % (i + 1, max_iter))
                self.n_iter_ += 1

        # calculate final perplexity value on train set
        doc_topics_distr, _ = self._e_step(
            X, cal_sstats=False, random_init=False, parallel=parallel
        )
        self.bound_ = self._perplexity_precomp_distr(
            X, doc_topics_distr, sub_sampling=False
        )

        return self
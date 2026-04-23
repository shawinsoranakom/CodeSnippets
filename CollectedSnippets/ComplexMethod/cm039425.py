def _fit_stages(
        self,
        X,
        y,
        raw_predictions,
        sample_weight,
        random_state,
        X_val,
        y_val,
        sample_weight_val,
        begin_at_stage=0,
        monitor=None,
    ):
        """Iteratively fits the stages.

        For each stage it computes the progress (OOB, train score)
        and delegates to ``_fit_stage``.
        Returns the number of stages fit; might differ from ``n_estimators``
        due to early stopping.
        """
        n_samples = X.shape[0]
        do_oob = self.subsample < 1.0
        sample_mask = np.ones((n_samples,), dtype=bool)
        n_inbag = max(1, int(self.subsample * n_samples))

        if self.verbose:
            verbose_reporter = VerboseReporter(verbose=self.verbose)
            verbose_reporter.init(self, begin_at_stage)

        X_csc = csc_array(X) if issparse(X) else None
        X_csr = csr_array(X) if issparse(X) else None

        if self.n_iter_no_change is not None:
            loss_history = np.full(self.n_iter_no_change, np.inf)
            # We create a generator to get the predictions for X_val after
            # the addition of each successive stage
            y_val_pred_iter = self._staged_raw_predict(X_val, check_input=False)

        # Older versions of GBT had its own loss functions. With the new common
        # private loss function submodule _loss, we often are a factor of 2
        # away from the old version. Here we keep backward compatibility for
        # oob_scores_ and oob_improvement_, even if the old way is quite
        # inconsistent (sometimes the gradient is half the gradient, sometimes
        # not).
        if isinstance(
            self._loss,
            (
                HalfSquaredError,
                HalfBinomialLoss,
            ),
        ):
            factor = 2
        else:
            factor = 1

        # perform boosting iterations
        i = begin_at_stage
        for i in range(begin_at_stage, self.n_estimators):
            # subsampling
            if do_oob:
                sample_mask = _random_sample_mask(n_samples, n_inbag, random_state)
                y_oob_masked = y[~sample_mask]
                sample_weight_oob_masked = sample_weight[~sample_mask]
                if i == 0:  # store the initial loss to compute the OOB score
                    initial_loss = factor * self._loss(
                        y_true=y_oob_masked,
                        raw_prediction=raw_predictions[~sample_mask],
                        sample_weight=sample_weight_oob_masked,
                    )

            # fit next stage of trees
            raw_predictions = self._fit_stage(
                i,
                X,
                y,
                raw_predictions,
                sample_weight,
                sample_mask,
                random_state,
                X_csc=X_csc,
                X_csr=X_csr,
            )

            # track loss
            if do_oob:
                self.train_score_[i] = factor * self._loss(
                    y_true=y[sample_mask],
                    raw_prediction=raw_predictions[sample_mask],
                    sample_weight=sample_weight[sample_mask],
                )
                self.oob_scores_[i] = factor * self._loss(
                    y_true=y_oob_masked,
                    raw_prediction=raw_predictions[~sample_mask],
                    sample_weight=sample_weight_oob_masked,
                )
                previous_loss = initial_loss if i == 0 else self.oob_scores_[i - 1]
                self.oob_improvement_[i] = previous_loss - self.oob_scores_[i]
                self.oob_score_ = self.oob_scores_[-1]
            else:
                # no need to fancy index w/ no subsampling
                self.train_score_[i] = factor * self._loss(
                    y_true=y,
                    raw_prediction=raw_predictions,
                    sample_weight=sample_weight,
                )

            if self.verbose > 0:
                verbose_reporter.update(i, self)

            if monitor is not None:
                early_stopping = monitor(i, self, locals())
                if early_stopping:
                    break

            # We also provide an early stopping based on the score from
            # validation set (X_val, y_val), if n_iter_no_change is set
            if self.n_iter_no_change is not None:
                # By calling next(y_val_pred_iter), we get the predictions
                # for X_val after the addition of the current stage
                validation_loss = factor * self._loss(
                    y_val, next(y_val_pred_iter), sample_weight_val
                )

                # Require validation_score to be better (less) than at least
                # one of the last n_iter_no_change evaluations
                if np.any(validation_loss + self.tol < loss_history):
                    loss_history[i % len(loss_history)] = validation_loss
                else:
                    break

        return i + 1
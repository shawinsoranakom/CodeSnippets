def _fit_stage(
        self,
        i,
        X,
        y,
        raw_predictions,
        sample_weight,
        sample_mask,
        random_state,
        X_csc=None,
        X_csr=None,
    ):
        """Fit another stage of ``n_trees_per_iteration_`` trees."""
        original_y = y

        if isinstance(self._loss, HuberLoss):
            set_huber_delta(
                loss=self._loss,
                y_true=y,
                raw_prediction=raw_predictions,
                sample_weight=sample_weight,
            )
        # TODO: Without oob, i.e. with self.subsample = 1.0, we could call
        # self._loss.loss_gradient and use it to set train_score_.
        # But note that train_score_[i] is the score AFTER fitting the i-th tree.
        # Note: We need the negative gradient!
        neg_gradient = -self._loss.gradient(
            y_true=y,
            raw_prediction=raw_predictions,
            sample_weight=None,  # We pass sample_weights to the tree directly.
        )
        # 2-d views of shape (n_samples, n_trees_per_iteration_) or (n_samples, 1)
        # on neg_gradient to simplify the loop over n_trees_per_iteration_.
        if neg_gradient.ndim == 1:
            neg_g_view = neg_gradient.reshape((-1, 1))
        else:
            neg_g_view = neg_gradient

        for k in range(self.n_trees_per_iteration_):
            if self._loss.is_multiclass:
                y = np.array(original_y == k, dtype=np.float64)

            # induce regression tree on the negative gradient
            tree = DecisionTreeRegressor(
                criterion="squared_error",
                splitter="best",
                max_depth=self.max_depth,
                min_samples_split=self.min_samples_split,
                min_samples_leaf=self.min_samples_leaf,
                min_weight_fraction_leaf=self.min_weight_fraction_leaf,
                min_impurity_decrease=self.min_impurity_decrease,
                max_features=self.max_features,
                max_leaf_nodes=self.max_leaf_nodes,
                random_state=random_state,
                ccp_alpha=self.ccp_alpha,
            )

            if self.subsample < 1.0:
                # no inplace multiplication!
                sample_weight = sample_weight * sample_mask.astype(np.float64)

            X = X_csc if X_csc is not None else X
            tree.fit(
                X, neg_g_view[:, k], sample_weight=sample_weight, check_input=False
            )

            # update tree leaves
            X_for_tree_update = X_csr if X_csr is not None else X
            _update_terminal_regions(
                self._loss,
                tree.tree_,
                X_for_tree_update,
                y,
                neg_g_view[:, k],
                raw_predictions,
                sample_weight,
                sample_mask,
                learning_rate=self.learning_rate,
                k=k,
            )

            # add tree to ensemble
            self.estimators_[i, k] = tree

        return raw_predictions
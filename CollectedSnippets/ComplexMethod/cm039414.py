def fit(self, X, y, **fit_params):
        """Get common fit operations."""
        names, clfs = self._validate_estimators()

        if self.weights is not None and len(self.weights) != len(self.estimators):
            raise ValueError(
                "Number of `estimators` and weights must be equal; got"
                f" {len(self.weights)} weights, {len(self.estimators)} estimators"
            )

        if _routing_enabled():
            routed_params = process_routing(self, "fit", **fit_params)
        else:
            routed_params = Bunch()
            for name in names:
                routed_params[name] = Bunch(fit={})
                if "sample_weight" in fit_params:
                    routed_params[name].fit["sample_weight"] = fit_params[
                        "sample_weight"
                    ]

        self.estimators_ = Parallel(n_jobs=self.n_jobs)(
            delayed(_fit_single_estimator)(
                clone(clf),
                X,
                y,
                fit_params=routed_params[name]["fit"],
                message_clsname="Voting",
                message=self._log_message(name, idx + 1, len(clfs)),
            )
            for idx, (name, clf) in enumerate(zip(names, clfs))
            if clf != "drop"
        )

        self.named_estimators_ = Bunch()

        # Uses 'drop' as placeholder for dropped estimators
        est_iter = iter(self.estimators_)
        for name, est in self.estimators:
            current_est = est if est == "drop" else next(est_iter)
            self.named_estimators_[name] = current_est

            if hasattr(current_est, "feature_names_in_"):
                self.feature_names_in_ = current_est.feature_names_in_

        return self
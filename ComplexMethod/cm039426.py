def _validate_estimators(self):
        if len(self.estimators) == 0 or not all(
            isinstance(item, (tuple, list)) and isinstance(item[0], str)
            for item in self.estimators
        ):
            raise ValueError(
                "Invalid 'estimators' attribute, 'estimators' should be a "
                "non-empty list of (string, estimator) tuples."
            )
        names, estimators = zip(*self.estimators)
        # defined by MetaEstimatorMixin
        self._validate_names(names)

        has_estimator = any(est != "drop" for est in estimators)
        if not has_estimator:
            raise ValueError(
                "All estimators are dropped. At least one is required "
                "to be an estimator."
            )

        is_estimator_type = is_classifier if is_classifier(self) else is_regressor

        for est in estimators:
            if est != "drop" and not is_estimator_type(est):
                raise ValueError(
                    "The estimator {} should be a {}.".format(
                        est.__class__.__name__, is_estimator_type.__name__[3:]
                    )
                )

        return names, estimators
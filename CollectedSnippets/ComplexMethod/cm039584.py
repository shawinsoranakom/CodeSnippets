def _more_validate_params(self, for_partial_fit=False):
        """Validate input params."""
        if self.early_stopping and for_partial_fit:
            raise ValueError("early_stopping should be False with partial_fit")
        if self.learning_rate == "optimal" and self.alpha == 0:
            raise ValueError(
                "alpha must be > 0 since "
                "learning_rate is 'optimal'. alpha is used "
                "to compute the optimal learning rate."
            )
        # TODO: Consider whether pa1 and pa2 could also work for other losses.
        if self.learning_rate in ("pa1", "pa2"):
            if is_classifier(self):
                if self.loss != "hinge":
                    msg = (
                        f"Learning rate '{self.learning_rate}' only works with loss "
                        "'hinge'."
                    )
                    raise ValueError(msg)
            elif self.loss != "epsilon_insensitive":
                msg = (
                    f"Learning rate '{self.learning_rate}' only works with loss "
                    "'epsilon_insensitive'."
                )
                raise ValueError(msg)
        if self.penalty == "elasticnet" and self.l1_ratio is None:
            raise ValueError("l1_ratio must be set when penalty is 'elasticnet'")

        # raises ValueError if not registered
        self._get_penalty_type(self.penalty)
        self._get_learning_rate_type(self.learning_rate)
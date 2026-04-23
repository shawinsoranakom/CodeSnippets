def _clear_state(self):
        """Clear the state of the gradient boosting model."""
        if hasattr(self, "estimators_"):
            self.estimators_ = np.empty((0, 0), dtype=object)
        if hasattr(self, "train_score_"):
            del self.train_score_
        if hasattr(self, "oob_improvement_"):
            del self.oob_improvement_
        if hasattr(self, "oob_scores_"):
            del self.oob_scores_
        if hasattr(self, "oob_score_"):
            del self.oob_score_
        if hasattr(self, "init_"):
            del self.init_
        if hasattr(self, "_rng"):
            del self._rng
def _update_no_improvement_count(self, early_stopping, X, y, sample_weight):
        if early_stopping:
            # compute validation score (can be NaN), use that for stopping
            val_score = self._score(X, y, sample_weight=sample_weight)

            self.validation_scores_.append(val_score)

            if self.verbose:
                print("Validation score: %f" % self.validation_scores_[-1])
            # update best parameters
            # use validation_scores_, not loss_curve_
            # let's hope no-one overloads .score with mse
            last_valid_score = self.validation_scores_[-1]

            if last_valid_score < (self.best_validation_score_ + self.tol):
                self._no_improvement_count += 1
            else:
                self._no_improvement_count = 0

            if last_valid_score > self.best_validation_score_:
                self.best_validation_score_ = last_valid_score
                self._best_coefs = [c.copy() for c in self.coefs_]
                self._best_intercepts = [i.copy() for i in self.intercepts_]
        else:
            if self.loss_curve_[-1] > self.best_loss_ - self.tol:
                self._no_improvement_count += 1
            else:
                self._no_improvement_count = 0
            if self.loss_curve_[-1] < self.best_loss_:
                self.best_loss_ = self.loss_curve_[-1]
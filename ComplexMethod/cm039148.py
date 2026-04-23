def _minibatch_convergence(
        self, X, batch_cost, H, H_buffer, n_samples, step, n_steps
    ):
        """Helper function to encapsulate the early stopping logic"""
        batch_size = X.shape[0]

        # counts steps starting from 1 for user friendly verbose mode.
        step = step + 1

        # Ignore first iteration because H is not updated yet.
        if step == 1:
            if self.verbose:
                print(f"Minibatch step {step}/{n_steps}: mean batch cost: {batch_cost}")
            return False

        # Compute an Exponentially Weighted Average of the cost function to
        # monitor the convergence while discarding minibatch-local stochastic
        # variability: https://en.wikipedia.org/wiki/Moving_average
        if self._ewa_cost is None:
            self._ewa_cost = batch_cost
        else:
            alpha = batch_size / (n_samples + 1)
            alpha = min(alpha, 1)
            self._ewa_cost = self._ewa_cost * (1 - alpha) + batch_cost * alpha

        # Log progress to be able to monitor convergence
        if self.verbose:
            print(
                f"Minibatch step {step}/{n_steps}: mean batch cost: "
                f"{batch_cost}, ewa cost: {self._ewa_cost}"
            )

        # Early stopping based on change of H
        H_diff = linalg.norm(H - H_buffer) / linalg.norm(H)
        if self.tol > 0 and H_diff <= self.tol:
            if self.verbose:
                print(f"Converged (small H change) at step {step}/{n_steps}")
            return True

        # Early stopping heuristic due to lack of improvement on smoothed
        # cost function
        if self._ewa_cost_min is None or self._ewa_cost < self._ewa_cost_min:
            self._no_improvement = 0
            self._ewa_cost_min = self._ewa_cost
        else:
            self._no_improvement += 1

        if (
            self.max_no_improvement is not None
            and self._no_improvement >= self.max_no_improvement
        ):
            if self.verbose:
                print(
                    "Converged (lack of improvement in objective function) "
                    f"at step {step}/{n_steps}"
                )
            return True

        return False
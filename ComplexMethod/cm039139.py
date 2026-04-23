def _check_convergence(
        self, X, batch_cost, new_dict, old_dict, n_samples, step, n_steps
    ):
        """Helper function to encapsulate the early stopping logic.

        Early stopping is based on two factors:
        - A small change of the dictionary between two minibatch updates. This is
          controlled by the tol parameter.
        - No more improvement on a smoothed estimate of the objective function for a
          a certain number of consecutive minibatch updates. This is controlled by
          the max_no_improvement parameter.
        """
        batch_size = X.shape[0]

        # counts steps starting from 1 for user friendly verbose mode.
        step = step + 1

        # Ignore 100 first steps or 1 epoch to avoid initializing the ewa_cost with a
        # too bad value
        if step <= min(100, n_samples / batch_size):
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

        if self.verbose:
            print(
                f"Minibatch step {step}/{n_steps}: mean batch cost: "
                f"{batch_cost}, ewa cost: {self._ewa_cost}"
            )

        # Early stopping based on change of dictionary
        dict_diff = linalg.norm(new_dict - old_dict) / self._n_components
        if self.tol > 0 and dict_diff <= self.tol:
            if self.verbose:
                print(f"Converged (small dictionary change) at step {step}/{n_steps}")
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
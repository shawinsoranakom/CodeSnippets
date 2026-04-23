def jax_state_sync(self):
        if not getattr(self, "_jax_state", None) or self._jax_state_synced:
            return

        trainable_variables = self._jax_state.get("trainable_variables", None)
        non_trainable_variables = self._jax_state.get(
            "non_trainable_variables", None
        )
        optimizer_variables = self._jax_state.get("optimizer_variables", None)
        metrics_variables = self._jax_state.get("metrics_variables", None)
        if trainable_variables:
            for ref_v, v in zip(self.trainable_variables, trainable_variables):
                ref_v.assign(v)
        if non_trainable_variables:
            for ref_v, v in zip(
                self.non_trainable_variables, non_trainable_variables
            ):
                ref_v.assign(v)
        if optimizer_variables:
            for ref_v, v in zip(self.optimizer.variables, optimizer_variables):
                ref_v.assign(v)
        if metrics_variables:
            for ref_v, v in zip(self.metrics_variables, metrics_variables):
                ref_v.assign(v)
        self._jax_state_synced = True
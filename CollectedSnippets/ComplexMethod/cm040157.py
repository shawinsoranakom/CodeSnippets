def apply(self, grads, trainable_variables=None):
        """Update traininable variables according to provided gradient values.

        `grads` should be a list of gradient tensors
        with 1:1 mapping to the list of variables the optimizer was built with.

        `trainable_variables` can be provided
        on the first call to build the optimizer.
        """
        if len(grads) == 0:
            # It is possible that the grad is empty. In this case,
            # `apply_gradients` is a no-op.
            return

        if trainable_variables is None:
            if not self.built:
                raise ValueError(
                    "When passing `grads` without `variables`, the optimizer "
                    "must already be built on a list of variables. "
                    "Call `optimizer.build(trainable_variables)` first. "
                )
            if len(grads) != len(self._trainable_variables_indices):
                raise ValueError(
                    "When passing `grads` as a list of gradient tensors, the "
                    f"gradients must match `optimizer.variables` one-to-on. "
                    f"Received a list of {len(grads)} gradients, but the "
                    f"optimizer is tracking {len(self._trainable_variables)} "
                    "trainable variables."
                )
            trainable_variables = self._trainable_variables
        else:
            trainable_variables = list(trainable_variables)
            # Optionally build optimizer.
            if not self.built:
                with backend.name_scope(self.name, caller=self):
                    self.build(trainable_variables)
                self.built = True
            self._check_variables_are_known(trainable_variables)

        with backend.name_scope(self.name, caller=self):
            # Filter empty gradients.
            grads, trainable_variables = self._filter_empty_gradients(
                grads, trainable_variables
            )

            # Overwrite targeted variables directly with their gradients if
            # their `overwrite_with_gradient` is set.
            grads, trainable_variables = (
                self._overwrite_variables_directly_with_gradients(
                    grads, trainable_variables
                )
            )

            if len(list(grads)) > 0:
                # Unscale gradients.
                scale = self.loss_scale_factor
                if scale is not None:
                    grads = [g if g is None else g / scale for g in grads]

                # Apply gradient updates.
                self._backend_apply_gradients(grads, trainable_variables)
                # Apply variable constraints after applying gradients.
                for variable in trainable_variables:
                    if variable.constraint is not None:
                        variable.assign(variable.constraint(variable))

        # Update iteration counter.
        self._iterations.assign_add(1)
def call(self, inputs, training=False):
        def unwrap_variable(variable):
            return None if variable is None else variable.value

        call_args = []
        for argument_name in self.call_fn_arguments:
            if argument_name == "params":
                call_args.append(
                    jax.tree_util.tree_map(unwrap_variable, self.params)
                )
            elif argument_name == "state":
                call_args.append(
                    jax.tree_util.tree_map(unwrap_variable, self.state)
                )
            elif argument_name == "rng":
                call_args.append(
                    jax.tree_util.tree_map(
                        _convert_to_jax_key, self._get_call_rng(training)
                    )
                )
            elif argument_name == "inputs":
                call_args.append(inputs)
            elif argument_name == "training":
                if backend.backend() == "jax":
                    call_args.append(training)

        def assign_state_to_variable(value, variable):
            # This exists only to make debugging this error case easier.
            if not hasattr(variable, "assign"):
                raise ValueError(
                    "Structure mismatch: the structure of the state returned "
                    "by `call` does not match the structure of the state at "
                    "initialization time."
                )
            variable.assign(value)

        def call_with_fn(fn):
            if self.call_fn_has_state:
                predictions, new_state = fn(*call_args)
                jax.tree_util.tree_map(
                    assign_state_to_variable, new_state, self.state
                )
                return predictions
            else:
                return fn(*call_args)

        if backend.backend() == "jax":
            return call_with_fn(self.call_fn)
        elif backend.backend() == "tensorflow":
            if training and self.jax2tf_training_true_fn is not None:
                return call_with_fn(self.jax2tf_training_true_fn)
            else:
                return call_with_fn(self.jax2tf_training_false_fn)
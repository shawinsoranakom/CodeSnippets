def build(self, input_shape):
        if (
            self.params is None
            and self.state is None
            and (self.call_fn_has_params or self.call_fn_has_state)
        ):
            self._initialize_weights(input_shape)

        if backend.backend() == "tensorflow":
            polymorphic_shapes = []
            for argument in self.call_fn_arguments:
                if argument == "inputs":
                    polymorphic_shapes.append(
                        self._get_jax2tf_input_shape(input_shape)
                    )
                elif argument != "training":
                    # params, state, rng
                    polymorphic_shapes.append("...")

            if "training" in self.call_fn_arguments:
                training_argument_index = self.call_fn_arguments.index(
                    "training"
                )
                self.jax2tf_training_false_fn = self._jax2tf_convert(
                    self._partial_with_positional(
                        self.call_fn, training_argument_index, False
                    ),
                    polymorphic_shapes,
                )
                self.jax2tf_training_true_fn = self._jax2tf_convert(
                    self._partial_with_positional(
                        self.call_fn, training_argument_index, True
                    ),
                    polymorphic_shapes,
                )
            else:
                self.jax2tf_training_false_fn = self._jax2tf_convert(
                    self.call_fn,
                    polymorphic_shapes,
                )
                self.jax2tf_training_true_fn = None
            super().build(input_shape)
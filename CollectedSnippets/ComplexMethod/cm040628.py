def _initialize_weights(self, input_shape):
        if tf.inside_function():
            raise ValueError("'JaxLayer' cannot be built inside tf function")

        # Initialize `params` and `state` if needed by calling `init_fn`.
        def create_input(shape):
            shape = [d if d is not None else 1 for d in shape]
            return jax.numpy.ones(shape)

        init_inputs = tree.map_shape_structure(create_input, input_shape)
        if backend.backend() == "jax" and jax_utils.is_in_jax_tracing_scope(
            tree.flatten(init_inputs)[0]
        ):
            raise ValueError("'JaxLayer' cannot be built in a tracing scope")

        init_args = []
        for argument_name in self.init_fn_arguments:
            if argument_name == "rng":
                init_args.append(
                    jax.tree_util.tree_map(
                        lambda x: jax.numpy.array(_convert_to_jax_key(x)),
                        self._get_init_rng(),
                    )
                )
            elif argument_name == "inputs":
                init_args.append(init_inputs)
            elif argument_name == "training":
                init_args.append(True)

        init_result = self.init_fn(*init_args)
        if self.call_fn_has_state:
            init_params, init_state = init_result
        else:
            init_params, init_state = init_result, None

        self.tracked_params = self._create_variables(
            init_params, trainable=True
        )
        self.tracked_state = self._create_variables(init_state, trainable=False)
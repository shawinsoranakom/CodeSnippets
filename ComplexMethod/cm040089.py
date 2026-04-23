def call(
        self,
        sequences,
        initial_state=None,
        mask=None,
        training=False,
    ):
        timesteps = sequences.shape[1]
        if self.unroll and timesteps is None:
            raise ValueError(
                "Cannot unroll a RNN if the "
                "time dimension is undefined. \n"
                "- If using a Sequential model, "
                "specify the time dimension by passing "
                "an `Input()` as your first layer.\n"
                "- If using the functional API, specify "
                "the time dimension by passing a `shape` "
                "or `batch_shape` argument to your `Input()`."
            )

        if initial_state is None:
            if self.stateful:
                initial_state = self.states
            else:
                initial_state = self.get_initial_state(
                    batch_size=ops.shape(sequences)[0]
                )
        if self.stateful:
            actual_batch_size = sequences.shape[0]
            if (
                self._expected_batch_size is not None
                and actual_batch_size is not None
                and actual_batch_size != self._expected_batch_size
            ):
                raise ValueError(
                    f"If an RNN is stateful, the batch size of the "
                    f"input sequences must be the same as the batch "
                    f"size of the initial state. \n"
                    f"- Expected batch size: {self._expected_batch_size}\n"
                    f"- Received batch size: {actual_batch_size}"
                )

        # RNN expect the states in a list, even if single state.
        if not tree.is_nested(initial_state):
            initial_state = [initial_state]
        initial_state = list(initial_state)

        # Cast states to compute dtype.
        # Note that states may be deeply nested
        # (e.g. in the stacked cells case).
        initial_state = tree.map_structure(
            lambda x: backend.convert_to_tensor(
                x, dtype=self.cell.compute_dtype
            ),
            initial_state,
        )

        # Prepopulate the dropout state so that the inner_loop is stateless
        # this is particularly important for JAX backend.
        self._maybe_config_dropout_masks(
            self.cell, sequences[:, 0, :], initial_state
        )

        last_output, outputs, states = self.inner_loop(
            sequences=sequences,
            initial_state=initial_state,
            mask=mask,
            training=training,
        )
        last_output = ops.cast(last_output, self.compute_dtype)
        outputs = ops.cast(outputs, self.compute_dtype)
        states = tree.map_structure(
            lambda x: ops.cast(x, dtype=self.compute_dtype), states
        )
        self._maybe_reset_dropout_masks(self.cell)

        if self.stateful:
            for self_state, state in zip(
                tree.flatten(self.states), tree.flatten(states)
            ):
                self_state.assign(state)

        if self.return_sequences:
            output = outputs
        else:
            output = last_output

        if self.return_state:
            return output, *states
        return output
def call(
        self,
        sequences,
        initial_state=None,
        mask=None,
        training=None,
    ):
        kwargs = {}
        if self.forward_layer._call_has_training_arg:
            kwargs["training"] = training
        if self.forward_layer._call_has_mask_arg:
            kwargs["mask"] = mask

        if initial_state is not None:
            # initial_states are not keras tensors, eg eager tensor from np
            # array.  They are only passed in from kwarg initial_state, and
            # should be passed to forward/backward layer via kwarg
            # initial_state as well.
            forward_inputs, backward_inputs = sequences, sequences
            half = len(initial_state) // 2
            forward_state = initial_state[:half]
            backward_state = initial_state[half:]
        else:
            forward_inputs, backward_inputs = sequences, sequences
            forward_state, backward_state = None, None

        y = self.forward_layer(
            forward_inputs, initial_state=forward_state, **kwargs
        )
        y_rev = self.backward_layer(
            backward_inputs, initial_state=backward_state, **kwargs
        )

        if self.return_state:
            states = tuple(y[1:] + y_rev[1:])
            y = y[0]
            y_rev = y_rev[0]

        y = ops.cast(y, self.compute_dtype)
        y_rev = ops.cast(y_rev, self.compute_dtype)

        if self.return_sequences:
            y_rev = ops.flip(y_rev, axis=1)
        if self.merge_mode == "concat":
            output = ops.concatenate([y, y_rev], axis=-1)
        elif self.merge_mode == "sum":
            output = y + y_rev
        elif self.merge_mode == "ave":
            output = (y + y_rev) / 2
        elif self.merge_mode == "mul":
            output = y * y_rev
        elif self.merge_mode is None:
            output = (y, y_rev)
        else:
            raise ValueError(
                "Unrecognized value for `merge_mode`. "
                f"Received: {self.merge_mode}"
                'Expected one of {"concat", "sum", "ave", "mul"}.'
            )
        if self.return_state:
            if self.merge_mode is None:
                return output + states
            return (output,) + states
        return output
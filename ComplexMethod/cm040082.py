def inner_loop(self, sequences, initial_state, mask, training=False):
        if tree.is_nested(mask):
            mask = mask[0]

        if self.use_cudnn in ("auto", True):
            if not self.recurrent_dropout:
                try:
                    if training and self.dropout:
                        dp_mask = self.cell.get_dropout_mask(sequences[:, 0, :])
                        dp_mask = ops.expand_dims(dp_mask, axis=1)
                        dp_mask = ops.broadcast_to(
                            dp_mask, ops.shape(sequences)
                        )
                        dp_sequences = sequences * dp_mask
                    else:
                        dp_sequences = sequences

                    # Backends are allowed to specify (optionally) optimized
                    # implementation of the inner LSTM loop. In the case of
                    # TF for instance, it will leverage cuDNN when feasible, and
                    # it will raise NotImplementedError otherwise.
                    out = backend.lstm(
                        dp_sequences,
                        initial_state[0],
                        initial_state[1],
                        mask,
                        kernel=self.cell.kernel,
                        recurrent_kernel=self.cell.recurrent_kernel,
                        bias=self.cell.bias,
                        activation=self.cell.activation,
                        recurrent_activation=self.cell.recurrent_activation,
                        return_sequences=self.return_sequences,
                        go_backwards=self.go_backwards,
                        unroll=self.unroll,
                    )
                    # We disable jit_compile for the model in this case,
                    # since cuDNN ops aren't XLA compatible.
                    if backend.backend() == "tensorflow":
                        self.supports_jit = False
                    return out
                except NotImplementedError:
                    pass
        if self.use_cudnn is True:
            raise ValueError(
                "use_cudnn=True was specified, "
                "but cuDNN is not supported for this layer configuration "
                "with this backend. Pass use_cudnn='auto' to fallback "
                "to a non-cuDNN implementation."
            )
        return super().inner_loop(
            sequences, initial_state, mask=mask, training=training
        )
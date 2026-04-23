def call(self, inputs, mask=None):
        if mask is not None:
            if len(mask.shape) > len(inputs.shape):
                raise ValueError(
                    "The `mask` must be broadcastable to `inputs` "
                    "and must not have more dimensions. "
                    f"Received: inputs.shape={inputs.shape}, "
                    f"mask.shape={mask.shape}"
                )
            for m_dim, i_dim in zip(mask.shape[::-1], inputs.shape[::-1]):
                if m_dim is not None and i_dim is not None:
                    if m_dim != 1 and m_dim != i_dim:
                        raise ValueError(
                            "The `mask` must be broadcastable to "
                            "`inputs`. Each mask dimension must be 1 "
                            "or match the corresponding input "
                            "dimension. Received: "
                            f"inputs.shape={inputs.shape}, "
                            f"mask.shape={mask.shape}"
                        )
            # We keep the positions where the mask is True or > 0.5, and set the
            # other (masked) positions to -1e.9.
            if backend.standardize_dtype(mask.dtype) != "bool":
                mask = backend.numpy.greater(
                    mask, backend.cast(0.5, dtype=mask.dtype)
                )
            inputs = backend.numpy.where(
                mask, inputs, _large_negative_number(inputs.dtype)
            )
        if isinstance(self.axis, (tuple, list)):
            if len(self.axis) > 1:
                outputs = backend.numpy.exp(
                    inputs
                    - backend.math.logsumexp(
                        inputs, axis=self.axis, keepdims=True
                    )
                )
            else:
                outputs = activations.softmax(inputs, axis=self.axis[0])
        else:
            outputs = activations.softmax(inputs, axis=self.axis)

        # Free pre-softmax masked inputs to reduce peak memory.
        # Without this, the masked inputs, softmax outputs, and
        # post-masked outputs all exist simultaneously.
        del inputs

        if mask is not None:
            # Zero out masked positions in case the entire axis is masked
            # (where softmax would output a uniform distribution).
            outputs = backend.numpy.where(mask, outputs, 0.0)

        return outputs
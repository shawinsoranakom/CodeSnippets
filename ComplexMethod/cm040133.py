def compute_mask(self, inputs, mask=None):
        if mask is None:
            return None
        if not isinstance(mask, (tuple, list)):
            raise ValueError(f"`mask` should be a list. Received mask={mask}")
        if not isinstance(inputs, (tuple, list)):
            raise ValueError(
                f"`inputs` should be a list. Received: inputs={inputs}"
            )
        if len(mask) != len(inputs):
            raise ValueError(
                "The lists `inputs` and `mask` should have the same length. "
                f"Received: inputs={inputs} of length {len(inputs)}, and "
                f"mask={mask} of length {len(mask)}"
            )
        if all(m is None for m in mask):
            return None
        # Make a list of masks while making sure
        # the dimensionality of each mask
        # is the same as the corresponding input.
        masks = []
        for input_i, mask_i in zip(inputs, mask):
            if mask_i is None:
                # Input is unmasked. Append all 1s to masks,
                masks.append(ops.ones_like(input_i, dtype="bool"))
            elif mask_i.ndim < input_i.ndim:
                # Broadcast mask shape to match in a way where we capture the
                # input as a symbolic input in the op graph.
                mask_i = ops.logical_or(
                    ops.expand_dims(mask_i, axis=-1),
                    ops.zeros_like(input_i, dtype="bool"),
                )
                masks.append(mask_i)
            else:
                masks.append(mask_i)
        concatenated = ops.concatenate(masks, axis=self.axis)
        return ops.any(concatenated, axis=-1, keepdims=False)
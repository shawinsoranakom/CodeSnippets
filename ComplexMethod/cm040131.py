def compute_mask(self, inputs, mask=None):
        if mask is None:
            return None
        if not isinstance(mask, (tuple, list)):
            raise ValueError(f"`mask` should be a list. Received: mask={mask}")
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
        # Default implementation does an OR between the masks, which works
        # for `Add`, `Subtract`, `Average`, `Maximum`, `Minimum`, `Multiply`.
        if any(m is None for m in mask):
            return None
        output_mask = mask[0]
        for m in mask[1:]:
            output_mask = ops.logical_or(output_mask, m)
        return output_mask
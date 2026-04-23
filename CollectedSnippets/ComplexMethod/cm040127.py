def _apply_merge_op_and_or_mask(self, op_fn, inputs):
        """Merge a set of inputs by applying `op_fn` and ORing the masks.

        We use this for `Minimum` and `Maximum` as it handles the fact that
        there is no identity element. If applicable, the mask obtained by ORing
        all masks is set on the output.

        Args:
            op_fn: binary operation to apply to tensor pair.
            inputs: array of tensors to apply operation on.
        """
        output = None
        output_mask = None

        for x in inputs:
            mask = backend.get_keras_mask(x)
            if mask is not None:
                mask = ops.broadcast_to(ops.expand_dims(mask, -1), ops.shape(x))
            if output is None:
                output = x
                output_mask = mask
                continue
            if mask is not None:
                x = ops.where(mask, x, output)
            if output_mask is not None:
                output = ops.where(output_mask, output, x)
            if mask is not None and output_mask is not None:
                output_mask = ops.logical_or(output_mask, mask)
            else:
                output_mask = None
            output = op_fn(output, x)

        if output_mask is not None:
            output_mask = ops.any(output_mask, axis=-1, keepdims=False)
            backend.set_keras_mask(output, output_mask)
        return output
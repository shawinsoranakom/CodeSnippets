def _merge_function(self, inputs):
        masks = [backend.get_keras_mask(x) for x in inputs]
        has_output_mask = all(mask is not None for mask in masks)
        output = None
        output_mask = None

        for x, mask in zip(inputs, masks):
            if mask is not None:
                mask = ops.broadcast_to(ops.expand_dims(mask, -1), ops.shape(x))
                # Replace 0s with 1s outside of mask.
                x = ops.where(mask, x, ops.cast(1, x.dtype))
                if has_output_mask:
                    output_mask = (
                        mask
                        if output_mask is None
                        else ops.logical_or(output_mask, mask)
                    )
            output = x if output is None else ops.multiply(output, x)

        if has_output_mask:
            # Replace 1s with 0s outside of mask per standard masking rules.
            output = ops.where(output_mask, output, ops.cast(0, output.dtype))
            output_mask = ops.any(output_mask, axis=-1, keepdims=False)
            backend.set_keras_mask(output, output_mask)
        return output
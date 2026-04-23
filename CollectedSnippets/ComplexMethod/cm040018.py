def compute_output_shape(self, input_shape):
        if self.output_mode == "int":
            return input_shape

        # Calculate depth (number of bins)
        depth = (
            len(self.bin_boundaries) + 1
            if self.bin_boundaries is not None
            else self.num_bins
        )

        if self.output_mode == "one_hot":
            # For one_hot mode, add depth dimension
            # If last dimension is 1, replace it with depth, otherwise append
            if input_shape and input_shape[-1] == 1 and len(input_shape) > 1:
                return tuple(input_shape[:-1]) + (depth,)
            else:
                return tuple(input_shape) + (depth,)
        else:
            if input_shape and len(input_shape) >= 2:
                # Match to eager tensor, remove second and append depth
                out_shape = (
                    (input_shape[0],) + tuple(input_shape[2:]) + (depth,)
                )
                return out_shape
            else:
                return (depth,)
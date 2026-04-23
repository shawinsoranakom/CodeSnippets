def compute_output_shape(self, input_shape):
        if (
            not len(input_shape) == 2
            or not isinstance(input_shape[0], tuple)
            or not isinstance(input_shape[1], tuple)
        ):
            raise ValueError(
                "Expected as input a list/tuple of 2 tensors. "
                f"Received input_shape={input_shape}"
            )
        if input_shape[0][-1] != input_shape[1][-1]:
            raise ValueError(
                "Expected the two input tensors to have identical shapes. "
                f"Received input_shape={input_shape}"
            )

        if not input_shape:
            if self.output_mode == "int":
                return ()
            return (self.num_bins,)
        if self.output_mode == "int":
            return tuple(input_shape[0])

        if self.output_mode == "one_hot" and input_shape[0][-1] != 1:
            return tuple(input_shape[0]) + (self.num_bins,)

        return tuple(input_shape[0])[:-1] + (self.num_bins,)
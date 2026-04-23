def compute_output_shape(self,    # pylint:disable=arguments-differ
                             input_shape: tuple[int | None, ...]) -> tuple[int | None, ...]:
        """Computes the output shape of the layer.

        Assumes that the layer will be built to match that input shape provided.

        Parameters
        ----------
        input_shape: tuple or list of tuples
            Shape tuple (tuple of integers) or list of shape tuples (one per output tensor of the
            layer).  Shape tuples can include None for free dimensions, instead of an integer.

        Returns
        -------
        tuple
            An input shape tuple
        """
        if len(input_shape) != 4:
            raise ValueError("Inputs should have rank " +
                             str(4) +
                             "; Received input shape:", str(input_shape))

        retval: tuple[int | None, ...]
        if self.data_format == "channels_first":
            height = None
            width = None
            if input_shape[2] is not None:
                height = input_shape[2] * self.size[0]
            if input_shape[3] is not None:
                width = input_shape[3] * self.size[1]
            chs = input_shape[1]
            assert chs is not None
            channels = chs // self.size[0] // self.size[1]

            if channels * self.size[0] * self.size[1] != input_shape[1]:
                raise ValueError("channels of input and size are incompatible")

            retval = (input_shape[0],
                      channels,
                      height,
                      width)
        else:
            height = None
            width = None
            if input_shape[1] is not None:
                height = input_shape[1] * self.size[0]
            if input_shape[2] is not None:
                width = input_shape[2] * self.size[1]
            chs = input_shape[3]
            assert chs is not None
            channels = chs // self.size[0] // self.size[1]

            if channels * self.size[0] * self.size[1] != input_shape[3]:
                raise ValueError("channels of input and size are incompatible")

            retval = (input_shape[0],
                      height,
                      width,
                      channels)
        return retval
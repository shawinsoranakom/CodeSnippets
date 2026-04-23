def call(self, inputs: KerasTensor, *args, **kwargs  # pylint:disable=arguments-differ
             ) -> KerasTensor:
        """This is where the layer's logic lives.

        Parameters
        ----------
        inputs: :class:`keras.KerasTensor`
            Input tensor, or list/tuple of input tensors

        Returns
        -------
        :class:`keras.KerasTensor`
            A tensor or list/tuple of tensors
        """
        input_shape = inputs.shape
        if len(input_shape) != 4:
            raise ValueError("Inputs should have rank " +
                             str(4) +
                             "; Received input shape:", str(input_shape))

        out = None
        if self.data_format == "channels_first":
            batch_size, channels, height, width = input_shape
            assert height is not None and width is not None and channels is not None
            if batch_size is None:
                batch_size = -1
            r_height, r_width = self.size
            o_height, o_width = height * r_height, width * r_width
            o_channels = channels // (r_height * r_width)

            out = ops.reshape(inputs, (batch_size, r_height, r_width, o_channels, height, width))
            out = ops.transpose(out, (0, 3, 4, 1, 5, 2))
            out = ops.reshape(out, (batch_size, o_channels, o_height, o_width))
        elif self.data_format == "channels_last":
            batch_size, height, width, channels = input_shape
            assert height is not None and width is not None and channels is not None
            if batch_size is None:
                batch_size = -1
            r_height, r_width = self.size
            o_height, o_width = height * r_height, width * r_width
            o_channels = channels // (r_height * r_width)

            out = ops.reshape(inputs, (batch_size, height, width, r_height, r_width, o_channels))
            out = ops.transpose(out, (0, 1, 3, 2, 4, 5))
            out = ops.reshape(out, (batch_size, o_height, o_width, o_channels))
        assert out is not None
        return T.cast("KerasTensor", out)
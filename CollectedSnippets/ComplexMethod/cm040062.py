def test_conv1d_transpose_consistency(
        self, kernel_size, strides, padding, output_padding
    ):
        """Test conv transpose, on an 1D array of size 3, against several
        convolution parameters. In particular, tests if Torch inconsistencies
        are raised.
        """

        # output_padding cannot be greater than strides
        if isinstance(output_padding, int) and output_padding >= strides:
            pytest.skip(
                "`output_padding` greater than `strides` is not supported"
            )

        if backend.config.image_data_format() == "channels_last":
            input_shape = (1, 3, 1)
        else:
            input_shape = (1, 1, 3)

        input = np.ones(shape=input_shape)
        kernel_weights = np.arange(1, kernel_size + 1).reshape(
            (kernel_size, 1, 1)
        )

        # Expected result
        expected_res = np_conv1d_transpose(
            x=input,
            kernel_weights=kernel_weights,
            bias_weights=np.zeros(shape=(1,)),
            strides=strides,
            padding=padding,
            output_padding=output_padding,
            data_format=backend.config.image_data_format(),
            dilation_rate=1,
        )

        # keras layer
        kc_layer = layers.Conv1DTranspose(
            filters=1,
            kernel_size=kernel_size,
            strides=strides,
            padding=padding,
            output_padding=output_padding,
            dilation_rate=1,
        )
        kc_layer.build(input_shape=input_shape)
        kc_layer.kernel.assign(kernel_weights)

        # Special cases for Torch
        if backend.backend() == "torch":
            # Args that cause output_padding >= strides
            # are clamped with a warning.
            if (kernel_size, strides, padding, output_padding) in [
                (2, 1, "same", None),
                (4, 1, "same", None),
            ]:
                clamped_output_padding = strides - 1  # usually 0 when stride=1
                expected_res = np_conv1d_transpose(
                    x=input,
                    kernel_weights=kernel_weights,
                    bias_weights=np.zeros(shape=(1,)),
                    strides=strides,
                    padding=padding,
                    output_padding=clamped_output_padding,
                    data_format=backend.config.image_data_format(),
                    dilation_rate=1,
                )
                with pytest.warns(UserWarning):
                    kc_res = kc_layer(input)
                self.assertAllClose(kc_res, expected_res, atol=1e-5)
                return

            # torch_padding > 0 and torch_output_padding > 0 case
            # Torch output differs from TF.
            (
                torch_padding,
                torch_output_padding,
            ) = _convert_conv_transpose_padding_args_from_keras_to_torch(
                kernel_size=kernel_size,
                stride=strides,
                dilation_rate=1,
                padding=padding,
                output_padding=output_padding,
            )
            if torch_padding > 0 and torch_output_padding > 0:
                with pytest.raises(AssertionError):
                    kc_res = kc_layer(input)
                    self.assertAllClose(kc_res, expected_res, atol=1e-5)
                return

        # Compare results
        kc_res = kc_layer(input)
        self.assertAllClose(kc_res, expected_res, atol=1e-5)
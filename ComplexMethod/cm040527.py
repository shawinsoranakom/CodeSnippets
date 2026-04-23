def test_separable_conv(self):
        data_format = backend.config.image_data_format()
        # Test 1D max pooling.
        if data_format == "channels_last":
            input_shape = (2, 20, 3)
        else:
            input_shape = (2, 3, 20)
        inputs_1d = KerasTensor(input_shape)
        kernel = KerasTensor([4, 3, 2])
        pointwise_kernel = KerasTensor([1, 6, 5])
        self.assertEqual(
            knn.separable_conv(
                inputs_1d, kernel, pointwise_kernel, 1, padding="valid"
            ).shape,
            (2, 17, 5) if data_format == "channels_last" else (2, 5, 17),
        )
        self.assertEqual(
            knn.separable_conv(
                inputs_1d, kernel, pointwise_kernel, 1, padding="same"
            ).shape,
            (2, 20, 5) if data_format == "channels_last" else (2, 5, 20),
        )
        self.assertEqual(
            knn.separable_conv(
                inputs_1d, kernel, pointwise_kernel, 2, dilation_rate=2
            ).shape,
            (2, 7, 5) if data_format == "channels_last" else (2, 5, 7),
        )

        # Test 2D separable conv.
        if data_format == "channels_last":
            input_shape = (2, 10, 10, 3)
        else:
            input_shape = (2, 3, 10, 10)
        inputs_2d = KerasTensor(input_shape)
        kernel = KerasTensor([2, 2, 3, 2])
        pointwise_kernel = KerasTensor([1, 1, 6, 5])
        self.assertEqual(
            knn.separable_conv(
                inputs_2d, kernel, pointwise_kernel, 1, padding="valid"
            ).shape,
            (2, 9, 9, 5) if data_format == "channels_last" else (2, 5, 9, 9),
        )
        self.assertEqual(
            knn.separable_conv(
                inputs_2d, kernel, pointwise_kernel, (1, 2), padding="same"
            ).shape,
            (2, 10, 5, 5) if data_format == "channels_last" else (2, 5, 10, 5),
        )
        self.assertEqual(
            knn.separable_conv(
                inputs_2d, kernel, pointwise_kernel, 2, dilation_rate=(2, 1)
            ).shape,
            (2, 4, 5, 5) if data_format == "channels_last" else (2, 5, 4, 5),
        )
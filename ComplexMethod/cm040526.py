def test_depthwise_conv(self):
        data_format = backend.config.image_data_format()
        # Test 1D depthwise conv.
        if data_format == "channels_last":
            input_shape = (2, 20, 3)
        else:
            input_shape = (2, 3, 20)
        inputs_1d = KerasTensor(input_shape)
        kernel = KerasTensor([4, 3, 1])
        self.assertEqual(
            knn.depthwise_conv(inputs_1d, kernel, 1, padding="valid").shape,
            (2, 17, 3) if data_format == "channels_last" else (2, 3, 17),
        )
        self.assertEqual(
            knn.depthwise_conv(inputs_1d, kernel, (1,), padding="same").shape,
            (2, 20, 3) if data_format == "channels_last" else (2, 3, 20),
        )
        self.assertEqual(
            knn.depthwise_conv(inputs_1d, kernel, 2, dilation_rate=2).shape,
            (2, 7, 3) if data_format == "channels_last" else (2, 3, 7),
        )

        # Test 2D depthwise conv.
        if data_format == "channels_last":
            input_shape = (2, 10, 10, 3)
        else:
            input_shape = (2, 3, 10, 10)
        inputs_2d = KerasTensor(input_shape)
        kernel = KerasTensor([2, 2, 3, 1])
        self.assertEqual(
            knn.depthwise_conv(inputs_2d, kernel, 1, padding="valid").shape,
            (2, 9, 9, 3) if data_format == "channels_last" else (2, 3, 9, 9),
        )
        self.assertEqual(
            knn.depthwise_conv(inputs_2d, kernel, (1, 2), padding="same").shape,
            (2, 10, 5, 3) if data_format == "channels_last" else (2, 3, 10, 5),
        )
        self.assertEqual(
            knn.depthwise_conv(inputs_2d, kernel, 2, dilation_rate=2).shape,
            (2, 4, 4, 3) if data_format == "channels_last" else (2, 3, 4, 4),
        )
        self.assertEqual(
            knn.depthwise_conv(
                inputs_2d, kernel, 2, dilation_rate=(2, 1)
            ).shape,
            (2, 4, 5, 3) if data_format == "channels_last" else (2, 3, 4, 5),
        )
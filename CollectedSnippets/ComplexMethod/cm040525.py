def test_conv(self):
        data_format = backend.config.image_data_format()
        # Test 1D conv.
        if data_format == "channels_last":
            input_shape = (2, 20, 3)
        else:
            input_shape = (2, 3, 20)
        inputs_1d = KerasTensor(input_shape)
        kernel = KerasTensor([4, 3, 2])
        self.assertEqual(
            knn.conv(inputs_1d, kernel, 1, padding="valid").shape,
            (2, 17, 2) if data_format == "channels_last" else (2, 2, 17),
        )
        self.assertEqual(
            knn.conv(inputs_1d, kernel, 1, padding="same").shape,
            (2, 20, 2) if data_format == "channels_last" else (2, 2, 20),
        )
        self.assertEqual(
            knn.conv(inputs_1d, kernel, (2,), dilation_rate=2).shape,
            (2, 7, 2) if data_format == "channels_last" else (2, 2, 7),
        )

        # Test 2D conv.
        if data_format == "channels_last":
            input_shape = (2, 10, 10, 3)
        else:
            input_shape = (2, 3, 10, 10)
        inputs_2d = KerasTensor(input_shape)
        kernel = KerasTensor([2, 2, 3, 2])
        self.assertEqual(
            knn.conv(inputs_2d, kernel, 1, padding="valid").shape,
            (2, 9, 9, 2) if data_format == "channels_last" else (2, 2, 9, 9),
        )
        self.assertEqual(
            knn.conv(inputs_2d, kernel, 1, padding="same").shape,
            (
                (2, 10, 10, 2)
                if data_format == "channels_last"
                else (2, 2, 10, 10)
            ),
        )
        self.assertEqual(
            knn.conv(inputs_2d, kernel, (2, 1), dilation_rate=(2, 1)).shape,
            (2, 4, 9, 2) if data_format == "channels_last" else (2, 2, 4, 9),
        )

        # Test 3D conv.
        if data_format == "channels_last":
            input_shape = (2, 8, 8, 8, 3)
        else:
            input_shape = (2, 3, 8, 8, 8)
        inputs_3d = KerasTensor(input_shape)
        kernel = KerasTensor([3, 3, 3, 3, 2])
        self.assertEqual(
            knn.conv(inputs_3d, kernel, 1, padding="valid").shape,
            (
                (2, 6, 6, 6, 2)
                if data_format == "channels_last"
                else (2, 2, 6, 6, 6)
            ),
        )
        self.assertEqual(
            knn.conv(inputs_3d, kernel, (2, 1, 2), padding="same").shape,
            (
                (2, 4, 8, 4, 2)
                if data_format == "channels_last"
                else (2, 2, 4, 8, 4)
            ),
        )
        self.assertEqual(
            knn.conv(
                inputs_3d, kernel, 1, padding="valid", dilation_rate=(1, 2, 2)
            ).shape,
            (
                (2, 6, 4, 4, 2)
                if data_format == "channels_last"
                else (2, 2, 6, 4, 4)
            ),
        )
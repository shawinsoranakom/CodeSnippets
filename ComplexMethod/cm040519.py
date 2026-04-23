def test_conv(self):
        data_format = backend.config.image_data_format()
        # Test 1D conv.
        if data_format == "channels_last":
            input_shape = (None, 20, 3)
        else:
            input_shape = (None, 3, 20)
        inputs_1d = KerasTensor(input_shape)
        kernel = KerasTensor([4, 3, 2])
        for padding in ["valid", "VALID"]:
            self.assertEqual(
                knn.conv(inputs_1d, kernel, 1, padding=padding).shape,
                (
                    (None, 17, 2)
                    if data_format == "channels_last"
                    else (None, 2, 17)
                ),
            )
        for padding in ["same", "SAME"]:
            self.assertEqual(
                knn.conv(inputs_1d, kernel, 1, padding=padding).shape,
                (
                    (None, 20, 2)
                    if data_format == "channels_last"
                    else (None, 2, 20)
                ),
            )
        self.assertEqual(
            knn.conv(inputs_1d, kernel, (2,), dilation_rate=2).shape,
            (None, 7, 2) if data_format == "channels_last" else (None, 2, 7),
        )

        # Test 2D conv.
        if data_format == "channels_last":
            input_shape = (None, 10, None, 3)
        else:
            input_shape = (None, 3, 10, None)
        inputs_2d = KerasTensor(input_shape)
        kernel = KerasTensor([2, 2, 3, 2])
        for padding in ["valid", "VALID"]:
            self.assertEqual(
                knn.conv(inputs_2d, kernel, 1, padding=padding).shape,
                (
                    (None, 9, None, 2)
                    if data_format == "channels_last"
                    else (None, 2, 9, None)
                ),
            )
        for padding in ["same", "SAME"]:
            self.assertEqual(
                knn.conv(inputs_2d, kernel, 1, padding=padding).shape,
                (
                    (None, 10, None, 2)
                    if data_format == "channels_last"
                    else (None, 2, 10, None)
                ),
            )
        self.assertEqual(
            knn.conv(inputs_2d, kernel, (2, 1), dilation_rate=(2, 1)).shape,
            (
                (None, 4, None, 2)
                if data_format == "channels_last"
                else (None, 2, 4, None)
            ),
        )

        # Test 2D conv - H, W specified
        if data_format == "channels_last":
            input_shape = (None, 10, 10, 3)
        else:
            input_shape = (None, 3, 10, 10)
        inputs_2d = KerasTensor(input_shape)
        kernel = KerasTensor([2, 2, 3, 2])
        for padding in ["valid", "VALID"]:
            self.assertEqual(
                knn.conv(inputs_2d, kernel, 1, padding=padding).shape,
                (
                    (None, 9, 9, 2)
                    if data_format == "channels_last"
                    else (None, 2, 9, 9)
                ),
            )
        for padding in ["same", "SAME"]:
            self.assertEqual(
                knn.conv(inputs_2d, kernel, 1, padding=padding).shape,
                (
                    (None, 10, 10, 2)
                    if data_format == "channels_last"
                    else (None, 2, 10, 10)
                ),
            )
        self.assertEqual(
            knn.conv(inputs_2d, kernel, (2, 1), dilation_rate=(2, 1)).shape,
            (
                (None, 4, 9, 2)
                if data_format == "channels_last"
                else (None, 2, 4, 9)
            ),
        )

        # Test 3D conv.
        if data_format == "channels_last":
            input_shape = (None, 8, None, 8, 3)
        else:
            input_shape = (None, 3, 8, None, 8)
        inputs_3d = KerasTensor(input_shape)
        kernel = KerasTensor([3, 3, 3, 3, 2])
        for padding in ["valid", "VALID"]:
            self.assertEqual(
                knn.conv(inputs_3d, kernel, 1, padding=padding).shape,
                (
                    (None, 6, None, 6, 2)
                    if data_format == "channels_last"
                    else (None, 2, 6, None, 6)
                ),
            )
        for padding in ["same", "SAME"]:
            self.assertEqual(
                knn.conv(inputs_3d, kernel, (2, 1, 2), padding=padding).shape,
                (
                    (None, 4, None, 4, 2)
                    if data_format == "channels_last"
                    else (None, 2, 4, None, 4)
                ),
            )
        self.assertEqual(
            knn.conv(
                inputs_3d, kernel, 1, padding="valid", dilation_rate=(1, 2, 2)
            ).shape,
            (
                (None, 6, None, 4, 2)
                if data_format == "channels_last"
                else (None, 2, 6, None, 4)
            ),
        )
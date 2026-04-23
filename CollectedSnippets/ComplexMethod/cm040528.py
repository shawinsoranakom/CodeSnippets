def test_conv_transpose(self):
        data_format = backend.config.image_data_format()
        if data_format == "channels_last":
            input_shape = (2, 4, 3)
        else:
            input_shape = (2, 3, 4)
        inputs_1d = KerasTensor(input_shape)
        kernel = KerasTensor([2, 5, 3])
        self.assertEqual(
            knn.conv_transpose(inputs_1d, kernel, 2).shape,
            (2, 8, 5) if data_format == "channels_last" else (2, 5, 8),
        )
        self.assertEqual(
            knn.conv_transpose(inputs_1d, kernel, 2, padding="same").shape,
            (2, 8, 5) if data_format == "channels_last" else (2, 5, 8),
        )
        self.assertEqual(
            knn.conv_transpose(
                inputs_1d, kernel, 5, padding="valid", output_padding=4
            ).shape,
            (2, 21, 5) if data_format == "channels_last" else (2, 5, 21),
        )

        if data_format == "channels_last":
            input_shape = (2, 4, 4, 3)
        else:
            input_shape = (2, 3, 4, 4)
        inputs_2d = KerasTensor(input_shape)
        kernel = KerasTensor([2, 2, 5, 3])
        self.assertEqual(
            knn.conv_transpose(inputs_2d, kernel, 2).shape,
            (2, 8, 8, 5) if data_format == "channels_last" else (2, 5, 8, 8),
        )
        self.assertEqual(
            knn.conv_transpose(inputs_2d, kernel, (2, 2), padding="same").shape,
            (2, 8, 8, 5) if data_format == "channels_last" else (2, 5, 8, 8),
        )
        self.assertEqual(
            knn.conv_transpose(
                inputs_2d, kernel, (5, 5), padding="valid", output_padding=4
            ).shape,
            (
                (2, 21, 21, 5)
                if data_format == "channels_last"
                else (2, 5, 21, 21)
            ),
        )
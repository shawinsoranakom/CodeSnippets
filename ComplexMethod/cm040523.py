def test_max_pool(self):
        data_format = backend.config.image_data_format()
        if data_format == "channels_last":
            input_shape = (1, 8, 3)
        else:
            input_shape = (1, 3, 8)
        x = KerasTensor(input_shape)
        self.assertEqual(
            knn.max_pool(x, 2, 1).shape,
            (1, 7, 3) if data_format == "channels_last" else (1, 3, 7),
        )
        self.assertEqual(
            knn.max_pool(x, 2, 2, padding="same").shape,
            (1, 4, 3) if data_format == "channels_last" else (1, 3, 4),
        )

        if data_format == "channels_last":
            input_shape = (1, 8, 8, 3)
        else:
            input_shape = (1, 3, 8, 8)
        x = KerasTensor(input_shape)
        self.assertEqual(
            knn.max_pool(x, 2, 1).shape,
            (1, 7, 7, 3) if data_format == "channels_last" else (1, 3, 7, 7),
        )
        self.assertEqual(
            knn.max_pool(x, 2, 2, padding="same").shape,
            (1, 4, 4, 3) if data_format == "channels_last" else (1, 3, 4, 4),
        )
        self.assertEqual(
            knn.max_pool(x, (2, 2), (2, 2), padding="same").shape,
            (1, 4, 4, 3) if data_format == "channels_last" else (1, 3, 4, 4),
        )
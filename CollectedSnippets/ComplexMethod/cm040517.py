def test_max_pool(self):
        data_format = backend.config.image_data_format()
        if data_format == "channels_last":
            input_shape = (None, 8, 3)
        else:
            input_shape = (None, 3, 8)
        x = KerasTensor(input_shape)
        self.assertEqual(
            knn.max_pool(x, 2, 1).shape,
            (None, 7, 3) if data_format == "channels_last" else (None, 3, 7),
        )
        self.assertEqual(
            knn.max_pool(x, 2, 2, padding="same").shape,
            (None, 4, 3) if data_format == "channels_last" else (None, 3, 4),
        )

        if data_format == "channels_last":
            input_shape = (None, 8, None, 3)
        else:
            input_shape = (None, 3, 8, None)
        x = KerasTensor(input_shape)
        (
            self.assertEqual(knn.max_pool(x, 2, 1).shape, (None, 7, None, 3))
            if data_format == "channels_last"
            else (None, 3, 7, None)
        )
        self.assertEqual(
            knn.max_pool(x, 2, 2, padding="same").shape,
            (
                (None, 4, None, 3)
                if data_format == "channels_last"
                else (None, 3, 4, None)
            ),
        )
        self.assertEqual(
            knn.max_pool(x, (2, 2), (2, 2), padding="same").shape,
            (
                (None, 4, None, 3)
                if data_format == "channels_last"
                else (None, 3, 4, None)
            ),
        )
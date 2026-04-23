def test_nested_data(self, data_type):
        if data_type not in ("list", "dict", "nested_list", "nested_dict"):
            raise ValueError(
                "data_type must be one of 'list', 'dict', 'nested_list' or "
                f"'nested_dict'. Received: {data_type}"
            )

        class NestedSource(grain.sources.RandomAccessDataSource):
            def __init__(self, data_type):
                self.x = np.random.random((40, 4)).astype("float32")
                self.y = np.random.random((40, 2)).astype("float32")
                self.data_type = data_type

            def __len__(self):
                return len(self.x)

            def __getitem__(self, idx):
                x = self.x[idx]
                y = self.y[idx]
                if self.data_type == "list":
                    return x, y
                elif self.data_type == "dict":
                    return {"x": x, "y": y}
                elif self.data_type == "nested_list":
                    return x, (x, y)
                elif self.data_type == "nested_dict":
                    return {"data": {"x": x, "y": y}}

        dataset = grain.MapDataset.source(NestedSource(data_type)).batch(
            batch_size=4
        )
        adapter = grain_dataset_adapter.GrainDatasetAdapter(dataset)

        if backend.backend() == "tensorflow":
            it = adapter.get_tf_dataset()
            expected_class = tf.Tensor
        elif backend.backend() == "jax":
            it = adapter.get_jax_iterator()
            expected_class = np.ndarray
        elif backend.backend() == "torch":
            it = adapter.get_torch_dataloader()
            expected_class = torch.Tensor
        else:
            it = adapter.get_numpy_iterator()
            expected_class = np.ndarray

        for batch in it:
            if data_type == "list":
                self.assertEqual(len(batch), 2)
                bx, by = batch
            elif data_type == "dict":
                self.assertEqual(len(batch), 2)
                bx, by = batch["x"], batch["y"]
            elif data_type == "nested_list":
                self.assertEqual(len(batch), 2)
                bx, (_, by) = batch
            elif data_type == "nested_dict":
                self.assertEqual(len(batch["data"]), 2)
                bx, by = batch["data"]["x"], batch["data"]["y"]
            self.assertIsInstance(bx, expected_class)
            self.assertIsInstance(by, expected_class)
            self.assertEqual(bx.dtype, by.dtype)
            self.assertEqual(bx.shape, (4, 4))
            self.assertEqual(by.shape, (4, 2))
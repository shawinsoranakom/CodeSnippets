def test_split_dataset_nested_structures(self, structure_type):
        n_sample, left_size, right_size = 100, 0.2, 0.8
        features1 = np.random.sample((n_sample, 2))
        features2 = np.random.sample((n_sample, 10, 2))
        labels = np.random.sample((n_sample, 1))

        if backend.backend() != "torch":
            create_dataset_function = tf.data.Dataset.from_tensor_slices
            cardinality_function = tf.data.Dataset.cardinality
        else:
            create_dataset_function = MyTorchDataset
            cardinality_function = len

        if structure_type == "tuple":
            dataset = create_dataset_function(((features1, features2), labels))
        if structure_type == "dict":
            dataset = create_dataset_function(
                {"y": features2, "x": features1, "labels": labels}
            )
        if structure_type == "OrderedDict":
            dataset = create_dataset_function(
                collections.OrderedDict(
                    [("y", features2), ("x", features1), ("labels", labels)]
                )
            )

        dataset_left, dataset_right = split_dataset(
            dataset, left_size=left_size, right_size=right_size
        )
        self.assertEqual(
            int(cardinality_function(dataset_left)), int(n_sample * left_size)
        )
        self.assertEqual(
            int(cardinality_function(dataset_right)), int(n_sample * right_size)
        )
        for sample in itertools.chain(dataset_left, dataset_right):
            if structure_type in ("dict", "OrderedDict"):
                x, y, labels = sample["x"], sample["y"], sample["labels"]
            elif structure_type == "tuple":
                (x, y), labels = sample
            self.assertEqual(x.shape, (2,))
            self.assertEqual(y.shape, (10, 2))
            self.assertEqual(labels.shape, (1,))
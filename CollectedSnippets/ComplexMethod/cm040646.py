def test_split_dataset(
        self, dataset_type, features_shape, preferred_backend
    ):
        n_sample, left_size, right_size = 100, 0.2, 0.8
        features = np.random.sample((n_sample,) + features_shape)
        labels = np.random.sample((n_sample, 1))
        cardinality_function = (
            tf.data.Dataset.cardinality
            if (backend.backend() != "torch" and preferred_backend != "torch")
            else len
        )

        if dataset_type == "list":
            dataset = [features, labels]
        elif dataset_type == "tuple":
            dataset = (features, labels)
        elif dataset_type == "tensorflow":
            dataset = tf.data.Dataset.from_tensor_slices((features, labels))
        elif dataset_type == "torch":
            dataset = MyTorchDataset(features, labels)
            cardinality_function = len
        else:
            raise ValueError(f"Unknown dataset_type: {dataset_type}")

        dataset_left, dataset_right = split_dataset(
            dataset,
            left_size=left_size,
            right_size=right_size,
            preferred_backend=preferred_backend,
        )
        self.assertEqual(
            int(cardinality_function(dataset_left)), int(n_sample * left_size)
        )
        self.assertEqual(
            int(cardinality_function(dataset_right)), int(n_sample * right_size)
        )
        for sample in itertools.chain(dataset_left, dataset_right):
            self.assertEqual(sample[0].shape, features_shape)
            self.assertEqual(sample[1].shape, (1,))
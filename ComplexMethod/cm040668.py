def create_dataset(dataset_type, dataset_kwargs):
    if dataset_type == "np_array":
        return np.ones((100, 4)), np.zeros((100, 3))
    elif dataset_type == "native_array":
        return ops.ones((100, 4)), ops.zeros((100, 3))
    elif dataset_type == "py_dataset":
        return TestPyDataset(**dataset_kwargs), None
    elif dataset_type == "tf_dataset":
        import tensorflow as tf

        dataset = tf.data.Dataset.from_tensor_slices(
            (tf.ones((100, 4)), tf.zeros((100, 3)))
        ).batch(5)
        if dataset_kwargs.get("infinite", False):
            dataset = dataset.repeat()
        return dataset, None
    elif dataset_type == "torch_dataloader":
        import torch

        class TestIterableDataset(torch.utils.data.IterableDataset):
            def __iter__(self):
                for _ in range(20):
                    yield torch.ones((5, 4)), torch.zeros((5, 3))

        class TestIterableDatasetWithLen(TestIterableDataset):
            def __len__(self):
                return 20

        if dataset_kwargs.get("iterable", False):
            if dataset_kwargs.get("has_len", False):
                dataset = TestIterableDatasetWithLen()
            else:
                dataset = TestIterableDataset()
            return torch.utils.data.DataLoader(dataset), None
        else:
            dataset = torch.utils.data.TensorDataset(
                torch.ones((100, 4)), torch.zeros((100, 3))
            )
            return torch.utils.data.DataLoader(dataset, batch_size=5), None
    elif dataset_type == "generator":

        def generate_finite():
            for _ in range(20):
                yield ops.ones((5, 4)), ops.zeros((5, 3))

        def generate_infinite():
            while True:
                yield ops.ones((5, 4)), ops.zeros((5, 3))

        if dataset_kwargs.get("infinite", False):
            return generate_infinite(), None
        else:
            return generate_finite(), None
    elif dataset_type == "grain_dataset":
        import grain

        class TestIterableDataset(grain.sources.RandomAccessDataSource):
            def __init__(self):
                super().__init__()
                self.x = np.ones((100, 4)).astype("float32")
                self.y = np.zeros((100, 3)).astype("float32")

            def __len__(self):
                return len(self.x)

            def __getitem__(self, idx):
                return self.x[idx], self.y[idx]

        if dataset_kwargs.get("use_dataloader", False):
            source = TestIterableDataset()
            dataloader = grain.DataLoader(
                data_source=source,
                sampler=grain.samplers.IndexSampler(len(source), num_epochs=1),
                operations=[grain.transforms.Batch(batch_size=5)],
            )
            return dataloader, None
        else:
            dataset = grain.MapDataset.source(TestIterableDataset())
            if dataset_kwargs.get("has_len", False):
                dataset = dataset.to_iter_dataset()
            dataset = dataset.batch(5)
            return dataset, None
    else:
        raise ValueError(f"Invalid dataset type {dataset_type}")
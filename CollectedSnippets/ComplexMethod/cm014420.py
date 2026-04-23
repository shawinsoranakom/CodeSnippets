def __getitems__(self, indices: list):
        # add batched sampling support when parent datasets supports it.
        if isinstance(self.datasets, dict):
            dict_batch: list[_T_dict] = [{} for _ in indices]
            for k, dataset in self.datasets.items():
                if callable(getattr(dataset, "__getitems__", None)):
                    items = dataset.__getitems__(indices)  # type: ignore[attr-defined]
                    if len(items) != len(indices):
                        raise ValueError(
                            "Nested dataset's output size mismatch."
                            f" Expected {len(indices)}, got {len(items)}"
                        )
                    for data, d_sample in zip(items, dict_batch, strict=True):
                        d_sample[k] = data
                else:
                    for idx, d_sample in zip(indices, dict_batch, strict=True):
                        d_sample[k] = dataset[idx]
            return dict_batch

        # tuple data
        list_batch: list[list] = [[] for _ in indices]
        for dataset in self.datasets:
            if callable(getattr(dataset, "__getitems__", None)):
                items = dataset.__getitems__(indices)  # type: ignore[attr-defined]
                if len(items) != len(indices):
                    raise ValueError(
                        "Nested dataset's output size mismatch."
                        f" Expected {len(indices)}, got {len(items)}"
                    )
                for data, t_sample in zip(items, list_batch, strict=True):
                    t_sample.append(data)
            else:
                for idx, t_sample in zip(indices, list_batch, strict=True):
                    t_sample.append(dataset[idx])
        tuple_batch: list[_T_tuple] = [tuple(sample) for sample in list_batch]
        return tuple_batch
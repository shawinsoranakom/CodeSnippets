def _split_dataset_torch(
    dataset, left_size=None, right_size=None, shuffle=False, seed=None
):
    """Splits a dataset into a left half and a right half (e.g. train / test).

    Args:
        dataset:
            A `torch.utils.data.Dataset` object,
            or a list/tuple of arrays with the same length.
        left_size: If float (in the range `[0, 1]`), it signifies
            the fraction of the data to pack in the left dataset. If integer, it
            signifies the number of samples to pack in the left dataset. If
            `None`, defaults to the complement to `right_size`.
            Defaults to `None`.
        right_size: If float (in the range `[0, 1]`), it signifies
            the fraction of the data to pack in the right dataset.
            If integer, it signifies the number of samples to pack
            in the right dataset.
            If `None`, defaults to the complement to `left_size`.
            Defaults to `None`.
        shuffle: Boolean, whether to shuffle the data before splitting it.
        seed: A random seed for shuffling.

    Returns:
        A tuple of two `torch.utils.data.Dataset` objects:
        the left and right splits.
    """
    import torch
    from torch.utils.data import TensorDataset
    from torch.utils.data import random_split

    dataset_type_spec = _get_type_spec(dataset)
    if dataset_type_spec is None:
        raise TypeError(
            "The `dataset` argument must be a `torch.utils.data.Dataset`"
            " object, or a list/tuple of arrays."
            f" Received: dataset={dataset} of type {type(dataset)}"
        )

    if not isinstance(dataset, torch.utils.data.Dataset):
        if dataset_type_spec is np.ndarray:
            dataset = TensorDataset(torch.from_numpy(dataset))
        elif dataset_type_spec in (list, tuple):
            tensors = [torch.from_numpy(x) for x in dataset]
            dataset = TensorDataset(*tensors)
        elif is_tf_dataset(dataset):
            dataset_as_list = _convert_dataset_to_list(
                dataset, dataset_type_spec
            )
            tensors = [
                torch.from_numpy(np.array(sample))
                for sample in zip(*dataset_as_list)
            ]
            dataset = TensorDataset(*tensors)

    if right_size is None and left_size is None:
        raise ValueError(
            "At least one of the `left_size` or `right_size` "
            "must be specified. "
            "Received: left_size=None and right_size=None"
        )

    # Calculate total length and rescale split sizes
    total_length = len(dataset)
    left_size, right_size = _rescale_dataset_split_sizes(
        left_size, right_size, total_length
    )

    # Shuffle the dataset if required
    if shuffle:
        generator = torch.Generator()
        if seed is not None:
            generator.manual_seed(seed)
        else:
            generator.seed()
    else:
        generator = None

    left_split, right_split = random_split(
        dataset, [left_size, right_size], generator=generator
    )

    return left_split, right_split
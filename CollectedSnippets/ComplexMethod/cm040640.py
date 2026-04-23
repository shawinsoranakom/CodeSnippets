def _get_data_iterator_from_dataset(dataset, dataset_type_spec):
    """Get the iterator from a dataset.

    Args:
        dataset: A `tf.data.Dataset`, a `torch.utils.data.Dataset` object,
            or a list/tuple of arrays.
        dataset_type_spec: The type of the dataset.

    Returns:
        iterator: An `iterator` object.
    """
    if dataset_type_spec is list:
        if len(dataset) == 0:
            raise ValueError(
                "Received an empty list dataset. "
                "Please provide a non-empty list of arrays."
            )

        expected_shape = None
        for i, element in enumerate(dataset):
            if not isinstance(element, np.ndarray):
                raise ValueError(
                    "Expected a list of `numpy.ndarray` objects,"
                    f"Received: {type(element)} at index {i}."
                )
            if expected_shape is None:
                expected_shape = element.shape
            elif element.shape[0] != expected_shape[0]:
                raise ValueError(
                    "Received a list of NumPy arrays with different lengths."
                    f"Mismatch found at index {i}, "
                    f"Expected shape={expected_shape} "
                    f"Received shape={np.array(element).shape}."
                    "Please provide a list of NumPy arrays of the same length."
                )

        return iter(zip(*dataset))
    elif dataset_type_spec is tuple:
        if len(dataset) == 0:
            raise ValueError(
                "Received an empty list dataset."
                "Please provide a non-empty tuple of arrays."
            )

        expected_shape = None
        for i, element in enumerate(dataset):
            if not isinstance(element, np.ndarray):
                raise ValueError(
                    "Expected a tuple of `numpy.ndarray` objects,"
                    f"Received: {type(element)} at index {i}."
                )
            if expected_shape is None:
                expected_shape = element.shape
            elif element.shape[0] != expected_shape[0]:
                raise ValueError(
                    "Received a tuple of NumPy arrays with different lengths."
                    f"Mismatch found at index {i}, "
                    f"Expected shape={expected_shape} "
                    f"Received shape={np.array(element).shape}."
                    "Please provide a tuple of NumPy arrays of the same length."
                )

        return iter(zip(*dataset))
    elif is_tf_dataset(dataset):
        if is_batched(dataset):
            dataset = dataset.unbatch()
        return iter(dataset)

    elif is_torch_dataset(dataset):
        return iter(dataset)
    elif dataset_type_spec is np.ndarray:
        return iter(dataset)
    raise ValueError(f"Invalid dataset_type_spec: {dataset_type_spec}")
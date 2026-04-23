def _split_dataset_tf(
    dataset, left_size=None, right_size=None, shuffle=False, seed=None
):
    """Splits a dataset into a left half and a right half (e.g. train / test).

    Args:
        dataset:
            A `tf.data.Dataset` object,
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
        A tuple of two `tf.data.Dataset` objects:
        the left and right splits.
    """
    from keras.src.utils.module_utils import tensorflow as tf

    dataset_type_spec = _get_type_spec(dataset)

    if dataset_type_spec is None:
        raise TypeError(
            "The `dataset` argument must be either"
            "a `tf.data.Dataset` object, or"
            "a list/tuple of arrays. "
            f"Received: dataset={dataset} of type {type(dataset)}"
        )

    if right_size is None and left_size is None:
        raise ValueError(
            "At least one of the `left_size` or `right_size` "
            "must be specified. Received: left_size=None and "
            "right_size=None"
        )

    dataset_as_list = _convert_dataset_to_list(dataset, dataset_type_spec)

    if shuffle:
        if seed is None:
            seed = random.randint(0, int(1e6))
        random.seed(seed)
        random.shuffle(dataset_as_list)

    total_length = len(dataset_as_list)

    left_size, right_size = _rescale_dataset_split_sizes(
        left_size, right_size, total_length
    )
    left_split = list(dataset_as_list[:left_size])
    right_split = list(dataset_as_list[-right_size:])

    left_split = _restore_dataset_from_list(
        left_split, dataset_type_spec, dataset
    )
    right_split = _restore_dataset_from_list(
        right_split, dataset_type_spec, dataset
    )

    left_split = tf.data.Dataset.from_tensor_slices(left_split)
    right_split = tf.data.Dataset.from_tensor_slices(right_split)

    # apply batching to the splits if the dataset is batched
    if dataset_type_spec is tf.data.Dataset and is_batched(dataset):
        batch_size = get_batch_size(dataset)
        if batch_size is not None:
            left_split = left_split.batch(batch_size)
            right_split = right_split.batch(batch_size)

    left_split = left_split.prefetch(tf.data.AUTOTUNE)
    right_split = right_split.prefetch(tf.data.AUTOTUNE)
    return left_split, right_split
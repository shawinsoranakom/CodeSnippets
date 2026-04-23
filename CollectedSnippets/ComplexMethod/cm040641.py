def _get_next_sample(
    dataset_iterator,
    ensure_shape_similarity,
    data_size_warning_flag,
    start_time,
):
    """Yield data samples from the `dataset_iterator`.

    Args:
        dataset_iterator: An `iterator` object.
        ensure_shape_similarity: If set to `True`, the shape of
            the first sample will be used to validate the shape of rest of the
            samples. Defaults to `True`.
        data_size_warning_flag: If set to `True`, a warning will
            be issued if the dataset takes longer than 10 seconds to iterate.
            Defaults to `True`.
        start_time (float): the start time of the dataset iteration. this is
            used only if `data_size_warning_flag` is set to true.

    Yields:
        data_sample: The next sample.
    """
    from keras.src.trainers.data_adapters.data_adapter_utils import (
        is_tensorflow_tensor,
    )
    from keras.src.trainers.data_adapters.data_adapter_utils import (
        is_torch_tensor,
    )

    try:
        dataset_iterator = iter(dataset_iterator)
        first_sample = next(dataset_iterator)
        if (
            isinstance(first_sample, np.ndarray)
            or is_tensorflow_tensor(first_sample)
            or is_torch_tensor(first_sample)
        ):
            first_sample_shape = np.array(first_sample).shape
        else:
            first_sample_shape = None
            ensure_shape_similarity = False
        yield first_sample
    except StopIteration:
        raise ValueError(
            "Received an empty dataset. Argument `dataset` must "
            "be a non-empty list/tuple of `numpy.ndarray` objects "
            "or `tf.data.Dataset` objects."
        )

    for i, sample in enumerate(dataset_iterator):
        if ensure_shape_similarity:
            if first_sample_shape != np.array(sample).shape:
                raise ValueError(
                    "All `dataset` samples must have same shape, "
                    f"Expected shape: {np.array(first_sample).shape} "
                    f"Received shape: {np.array(sample).shape} at index "
                    f"{i}."
                )
        if data_size_warning_flag:
            if i % 10 == 0:
                cur_time = time.time()
                # warns user if the dataset is too large to iterate within 10s
                if int(cur_time - start_time) > 10 and data_size_warning_flag:
                    warnings.warn(
                        "The dataset is taking longer than 10 seconds to "
                        "iterate over. This may be due to the size of the "
                        "dataset. Keep in mind that the `split_dataset` "
                        "utility is only for small in-memory dataset "
                        "(e.g. < 10,000 samples).",
                        category=ResourceWarning,
                        source="split_dataset",
                    )
                    data_size_warning_flag = False
        yield sample
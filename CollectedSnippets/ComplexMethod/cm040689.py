def __init__(
        self,
        x,
        y=None,
        sample_weight=None,
        batch_size=None,
        steps=None,
        shuffle=False,
        class_weight=None,
    ):
        if not can_convert_arrays((x, y, sample_weight)):
            raise ValueError(
                "Expected all elements of `x` to be array-like. "
                f"Received invalid types: x={x}"
            )

        if sample_weight is not None:
            if class_weight is not None:
                raise ValueError(
                    "You cannot `class_weight` and `sample_weight` "
                    "at the same time."
                )
            if tree.is_nested(y):
                if isinstance(sample_weight, (list, tuple, dict)):
                    try:
                        tree.assert_same_structure(y, sample_weight)
                    except ValueError:
                        raise ValueError(
                            "You should provide one `sample_weight` array per "
                            "output in `y`. The two structures did not match:\n"
                            f"- y: {y}\n"
                            f"- sample_weight: {sample_weight}\n"
                        )
                else:
                    is_samplewise = len(sample_weight.shape) == 1 or (
                        len(sample_weight.shape) == 2
                        and sample_weight.shape[1] == 1
                    )
                    if not is_samplewise:
                        raise ValueError(
                            "For a model with multiple outputs, when providing "
                            "a single `sample_weight` array, it should only "
                            "have one scalar score per sample "
                            "(i.e. shape `(num_samples,)`). If you want to use "
                            "non-scalar sample weights, pass a `sample_weight` "
                            "argument with one array per model output."
                        )
                    # Replicate the same sample_weight array on all outputs.
                    sample_weight = tree.map_structure(
                        lambda _: sample_weight, y
                    )
        if class_weight is not None:
            if tree.is_nested(y):
                raise ValueError(
                    "`class_weight` is only supported for Models with a single "
                    "output."
                )
            sample_weight = data_adapter_utils.class_weight_to_sample_weights(
                y, class_weight
            )

        inputs = data_adapter_utils.pack_x_y_sample_weight(x, y, sample_weight)

        data_adapter_utils.check_data_cardinality(inputs)
        num_samples = set(
            i.shape[0] for i in tree.flatten(inputs) if i is not None
        ).pop()
        self._num_samples = num_samples
        self._inputs = inputs

        # If batch_size is not passed but steps is, calculate from the input
        # data.  Defaults to `32` for backwards compatibility.
        if not batch_size:
            batch_size = int(math.ceil(num_samples / steps)) if steps else 32

        self._size = int(math.ceil(num_samples / batch_size))
        self._batch_size = batch_size
        self._partial_batch_size = num_samples % batch_size
        self._shuffle = shuffle
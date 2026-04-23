def __init__(
      self,
      metric: tf_keras.metrics.Metric,
      slicing_spec: dict[str, str] | dict[str, int],
      slicing_feature_dtype: tf.DType | None = None,
      name: str | None = None,
  ):
    """Initializes the instance.

    Args:
      metric: A `tf_keras.metrics.Metric` instance.
      slicing_spec: A dictionary that maps from string slice names, to one of
        integer, boolean, or string slicing values.
      slicing_feature_dtype: The expected dtype of the slicing feature. The
        values in the slicing spec are casted to this type if passed. If None,
        the dtype of the slicing feature is inferred based on the values in the
        slicing spec.
      name: The name of the wrapper metric. Defaults to `sliced_{metric.name}`.

    Raises:
      A ValueError if `slicing_spec` is empty, contains duplicate slicing
      values, or has slicing values of different types.
    """
    super().__init__(name=name or f"sliced_{metric.name}", dtype=metric.dtype)

    if not slicing_spec:
      raise ValueError("The slicing spec must be a non-empty dictionary.")

    slice_names, slicing_values = zip(*slicing_spec.items())
    if not isinstance(slicing_values[0], (int, bool, str)) or not all(
        isinstance(k, type(slicing_values[0])) for k in slicing_values
    ):
      raise ValueError(
          "All slicing values in the slicing spec must be one of `int`, "
          "`bool`, or `str`, and all values must have the same type. "
          f"Got types: {list(map(type, slicing_values))}."
      )

    if len(slicing_values) > len(set(slicing_values)):
      raise ValueError(
          "The slicing values passed to the slicing spec must be unique. Got "
          f"{slicing_values}."
      )

    # TODO(b/276811843): Look into validating whether `metric` accepts
    # `sample_weights` in its `update_state` method.

    # Instance fully owns a deep copy of the metric.
    self._metric = copy.deepcopy(metric)
    self._slice_names = list(slice_names)
    self._slicing_values = list(slicing_values)
    self._slicing_values_tensors = [
        tf.constant(v, slicing_feature_dtype) for v in slicing_values
    ]
    self._slicing_feature_dtype = self._slicing_values_tensors[0].dtype
    self._sliced_metrics = [copy.deepcopy(metric) for _ in self._slicing_values]
def build(self, input_shapes: Mapping[str, tf.TensorShape]) -> None:
    missing_features = set(self._feature_names) - input_shapes.keys()
    if missing_features:
      raise ValueError(f"Layer inputs is missing features: {missing_features}")

    feature_shapes = {
        feature_name: tensor_shape
        for feature_name, tensor_shape in input_shapes.items()
        if feature_name in self._feature_names
    }

    most_specific_shape = tf.TensorShape(None)
    for feature_name, shape in feature_shapes.items():
      if not isinstance(shape, tf.TensorShape):
        raise TypeError(
            f"Got unsupported tensor shape type for feature {feature_name}. The"
            " feature tensor must be one of `tf.Tensor`, `tf.SparseTensor` or"
            " `tf.RaggedTensor`, with a well defined tensor shape but got shape"
            f" {shape} instead."
        )

      shape = shape[:-1]
      if shape.is_subtype_of(most_specific_shape):
        most_specific_shape = shape

      elif not most_specific_shape.is_subtype_of(shape):
        raise ValueError(
            "All features from the feature_names set must be tensors with the"
            " same shape except for the last dimension, but got features with"
            f" incompatible shapes {feature_shapes}"
        )

    super().build(input_shapes)
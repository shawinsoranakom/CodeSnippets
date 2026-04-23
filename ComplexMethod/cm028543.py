def __init__(
      self,
      input_params: exp_cfg.DataConfig,
  ):

    self._segment_labels = input_params.segment_labels
    self._feature_names = input_params.feature_names
    self._feature_sources = input_params.feature_sources
    self._feature_sizes = input_params.feature_sizes
    self._feature_dtypes = input_params.feature_dtypes
    self._feature_from_bytes = input_params.feature_from_bytes
    self._include_video_id = input_params.include_video_id
    self._label_field = input_params.label_field

    assert len(self._feature_names) == len(self._feature_sources), (
        "length of feature_names (={}) != length of feature_sizes (={})".format(
            len(self._feature_names), len(self._feature_sources)))

    self._context_features = {}
    self._sequence_features = {}
    if self._include_video_id:
      self._context_features["id"] = tf.io.FixedLenFeature([], tf.string)

    if self._segment_labels:
      self._context_features.update({
          # There is no need to read end-time given we always assume the segment
          # has the same size.
          "segment_labels": tf.io.VarLenFeature(tf.int64),
          "segment_start_times": tf.io.VarLenFeature(tf.int64),
          "segment_scores": tf.io.VarLenFeature(tf.float32)
      })
    else:
      self._add_labels_specification()

    for i, name in enumerate(self._feature_names):
      if self._feature_from_bytes[i]:
        feature_type = tf.io.FixedLenSequenceFeature([], dtype=tf.string)
      else:
        dtype = tf.dtypes.as_dtype(self._feature_dtypes[i])
        feature_shape = [self._feature_sizes[i]]
        if self._feature_sources[i] == "feature":
          feature_type = tf.io.FixedLenSequenceFeature(feature_shape, dtype)
        else:
          feature_type = tf.io.FixedLenFeature(feature_shape, dtype)
      if self._feature_sources[i] == "feature":
        self._sequence_features[name] = feature_type
      elif self._feature_sources[i] == "context":
        self._context_features[name] = feature_type
      else:
        raise ValueError(
            f"Unknown feature source {self._feature_sources[i]} for {name}")
def pad_to_max_size(features):
  """Pads features to max height and max width and stacks them up.

  Args:
    features: A list of num_levels 4D float tensors of shape [batch, height_i,
      width_i, channels] containing feature maps.

  Returns:
    stacked_features: A 5D float tensor of shape [batch, num_levels, max_height,
      max_width, channels] containing stacked features.
    true_feature_shapes: A 2D int32 tensor of shape [num_levels, 2] containing
      height and width of the feature maps before padding.
  """
  if len(features) == 1:
    return tf.expand_dims(features[0],
                          1), tf.expand_dims(tf.shape(features[0])[1:3], 0)

  if all([feature.shape.is_fully_defined() for feature in features]):
    heights = [feature.shape[1] for feature in features]
    widths = [feature.shape[2] for feature in features]
    max_height = max(heights)
    max_width = max(widths)
  else:
    heights = [tf.shape(feature)[1] for feature in features]
    widths = [tf.shape(feature)[2] for feature in features]
    max_height = tf.reduce_max(heights)
    max_width = tf.reduce_max(widths)
  features_all = [
      tf.image.pad_to_bounding_box(feature, 0, 0, max_height,
                                   max_width) for feature in features
  ]
  features_all = tf.stack(features_all, axis=1)
  true_feature_shapes = tf.stack([tf.shape(feature)[1:3]
                                  for feature in features])
  return features_all, true_feature_shapes
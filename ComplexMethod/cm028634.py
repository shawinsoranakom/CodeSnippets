def resize(feat,
           target_height,
           target_width,
           strategy,
           training=False,
           method='bilinear'):
  """Resizes the spitial dimensions."""
  dtype = feat.dtype
  feat_shape = feat.get_shape()
  if method == 'bilinear':
    if strategy == 'tpu' and training:
      if dtype == tf.bfloat16:
        feat = tf.cast(feat, tf.float32)
        feat = tf.image.resize(feat, [target_height, target_width])
        feat = tf.cast(feat, dtype)
      elif feat_shape.is_fully_defined():
        # Batch dimension is known. Mimic resize[h,w] with
        # resize[h,1]+resize[1,w] to reduce HBM padding.
        b, h, w, c = feat_shape.as_list()
        feat = tf.reshape(feat, [b, h, 1, -1])
        feat = tf.image.resize(feat, [target_height, 1])
        feat = tf.reshape(feat, [-1, 1, w, c])
        feat = tf.image.resize(feat, [1, target_width])
        feat = tf.reshape(feat, [b, target_height, target_width, c])
      else:
        feat = tf.image.resize(feat, [target_height, target_width])
    else:
      feat = tf.image.resize(feat, [target_height, target_width])
  elif method == 'nearest':
    _, h, w, _ = feat_shape.as_list()
    if training and target_height % h == 0 and target_width % w == 0:

      feat = resize_nearest_neighbor(feat, target_height // h,
                                     target_width // w)
    else:
      feat = tf.cast(feat, tf.float32)
      feat = tf.image.resize(feat, [target_height, target_width],
                             tf.image.ResizeMethod.NEAREST_NEIGHBOR)
  else:
    raise ValueError('Upsampling type {} is not supported.'.format(method))
  return tf.cast(feat, dtype)
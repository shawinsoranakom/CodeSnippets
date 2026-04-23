def ExtractGlobalFeatures(image,
                          image_scales,
                          global_scales_ind,
                          model_fn,
                          multi_scale_pool_type='None',
                          normalize_global_descriptor=False,
                          normalization_function=gld.NormalizeImages):
  """Extract global features for input image.

  Args:
    image: image tensor of type tf.uint8 with shape [h, w, channels].
    image_scales: 1D float tensor which contains float scales used for image
      pyramid construction.
    global_scales_ind: Feature extraction happens only for a subset of
      `image_scales`, those with corresponding indices from this tensor.
    model_fn: model function. Follows the signature:
      * Args:
        * `images`: Batched image tensor.
      * Returns:
        * `global_descriptors`: Global descriptors for input images.
    multi_scale_pool_type: If set, the global descriptor of each scale is pooled
      and a 1D global descriptor is returned.
    normalize_global_descriptor: If True, output global descriptors are
      L2-normalized.
    normalization_function: Function used for normalization.

  Returns:
    global_descriptors: If `multi_scale_pool_type` is 'None', returns a [S, D]
      float tensor. S is the number of scales, and D the global descriptor
      dimensionality. Each D-dimensional entry is a global descriptor, which may
      be L2-normalized depending on `normalize_global_descriptor`. If
      `multi_scale_pool_type` is not 'None', returns a [D] float tensor with the
      pooled global descriptor.

  """
  original_image_shape_float = tf.gather(
      tf.dtypes.cast(tf.shape(image), tf.float32), [0, 1])
  image_tensor = normalization_function(
      image, pixel_value_offset=128.0, pixel_value_scale=128.0)
  image_tensor = tf.expand_dims(image_tensor, 0, name='image/expand_dims')

  def _ResizeAndExtract(scale_index):
    """Helper function to resize image then extract global feature.

    Args:
      scale_index: A valid index in image_scales.

    Returns:
      global_descriptor: [1,D] tensor denoting the extracted global descriptor.
    """
    scale = tf.gather(image_scales, scale_index)
    new_image_size = tf.dtypes.cast(
        tf.round(original_image_shape_float * scale), tf.int32)
    resized_image = tf.image.resize(image_tensor, new_image_size)
    global_descriptor = model_fn(resized_image)
    return global_descriptor

  # First loop to find initial scale to be used.
  num_scales = tf.shape(image_scales)[0]
  initial_scale_index = tf.constant(-1, dtype=tf.int32)
  for scale_index in tf.range(num_scales):
    if tf.reduce_any(tf.equal(global_scales_ind, scale_index)):
      initial_scale_index = scale_index
      break

  output_global = _ResizeAndExtract(initial_scale_index)

  # Loop over subsequent scales.
  for scale_index in tf.range(initial_scale_index + 1, num_scales):
    # Allow an undefined number of global feature scales to be extracted.
    tf.autograph.experimental.set_loop_options(
        shape_invariants=[(output_global, tf.TensorShape([None, None]))])

    if tf.reduce_any(tf.equal(global_scales_ind, scale_index)):
      global_descriptor = _ResizeAndExtract(scale_index)
      output_global = tf.concat([output_global, global_descriptor], 0)

  normalization_axis = 1
  if multi_scale_pool_type == 'average':
    output_global = tf.reduce_mean(
        output_global,
        axis=0,
        keepdims=False,
        name='multi_scale_average_pooling')
    normalization_axis = 0
  elif multi_scale_pool_type == 'sum':
    output_global = tf.reduce_sum(
        output_global, axis=0, keepdims=False, name='multi_scale_sum_pooling')
    normalization_axis = 0

  if normalize_global_descriptor:
    output_global = tf.nn.l2_normalize(
        output_global, axis=normalization_axis, name='l2_normalization')

  return output_global
def bilinear_resize_to_bbox(
    images: tf.Tensor, bbox: tf.Tensor, output_size: tf.Tensor
) -> tf.Tensor:
  """Bilinear resizes the images to fit into the bounding boxes in the output.

  Args:
    images: A tensor in shape (batch_size, input_h, input_w, ...) with arbitrary
      numbers of channel dimensions.
    bbox: A tensor in shape (batch_size, 4), representing the absolute
      coordinates (ymin, xmin, ymax, xmax) for each bounding box.
    output_size: The size of the output images in (output_h, output_w).

  Returns:
    A tensor in shape (batch_size, output_h, output_w, ...). The result has the
    same dtype as the input if it's float32, float16, bfloat16, otherwise the
    result is float32.
  """
  images_shape = images.get_shape().as_list()
  images_rank = len(images_shape)
  if images_rank < 3:
    raise ValueError(
        'Expected the input images (batch_size, height, width, ...) '
        'has rank >= 3, was: %s' % images_shape)
  bbox_shape = bbox.get_shape().as_list()
  if bbox_shape[-1] != 4:
    raise ValueError(
        'Expected the last dimension of `bbox` has size == 4, but the shape '
        'of `bbox` was: %s' % bbox_shape)

  rank_range = list(range(images_rank))
  extra_dims = images_shape[3:]
  extra_dims_perm = rank_range[3:]
  extra_dims_product = 1
  for d in extra_dims:
    extra_dims_product *= d

  input_h = tf.cast(tf.shape(images)[1], tf.float32)
  input_w = tf.cast(tf.shape(images)[2], tf.float32)
  output_h = output_size[0]
  output_w = output_size[1]

  bbox = tf.cast(bbox, tf.float32)
  # (batch_size, 1)
  bbox_ymin = bbox[:, 0:1]
  bbox_xmin = bbox[:, 1:2]
  bbox_ymax = bbox[:, 2:3]
  bbox_xmax = bbox[:, 3:4]
  bbox_h = bbox_ymax - bbox_ymin
  bbox_w = bbox_xmax - bbox_xmin
  scale_h = tf.math.divide_no_nan(input_h, bbox_h)
  scale_w = tf.math.divide_no_nan(input_w, bbox_w)

  # Generates the output grids.
  # (output_h)
  output_y_grid = tf.range(output_h, dtype=bbox_ymin.dtype)
  # (output_w)
  output_x_grid = tf.range(output_w, dtype=bbox_xmin.dtype)

  # Computes the input source positions (float) which map to the output grids
  # (integer).
  # Applies half pixel offset here to ensure the output is center-aligned to the
  # input.
  # TODO(b/245614786): support align_corners=True.
  # (batch_size, output_h)
  input_y_pos = tf.clip_by_value(
      (output_y_grid - bbox_ymin + 0.5) * scale_h - 0.5, 0.0, input_h - 1.0)
  # (batch_size, output_w)
  input_x_pos = tf.clip_by_value(
      (output_x_grid - bbox_xmin + 0.5) * scale_w - 0.5, 0.0, input_w - 1.0)

  # Gets the positions (integer) of the four nearest neighbors of the input
  # source position (float).
  # (y0, x0): left-top
  # (y0, x1): right-top
  # (y1, x0): left-bottom
  # (y1, x1): right-bottom
  # (batch_size, output_h)
  input_y0 = tf.cast(
      tf.clip_by_value(tf.floor(input_y_pos), 0.0, input_h - 2.0), tf.int32)
  input_y1 = input_y0 + 1
  # (batch_size, output_w)
  input_x0 = tf.cast(
      tf.clip_by_value(tf.floor(input_x_pos), 0.0, input_w - 2.0), tf.int32)
  input_x1 = input_x0 + 1

  # (batch_size, output_h)
  output_y_mask = (bbox_ymin <= output_y_grid) & (output_y_grid < bbox_ymax)
  # (batch_size, output_w)
  output_x_mask = (bbox_xmin <= output_x_grid) & (output_x_grid < bbox_xmax)

  # Masks the output pixels outside the bounding box by setting their input
  # neighbors to -1. This makes `tf.one_hot` operation produce all zeros at
  # these pixels, so as to accelerate the sparse matrix multiplication in
  # `_gather_rows_from_matrix`.
  # (batch_size, output_h)
  input_y0 = tf.where(output_y_mask, input_y0, -tf.ones_like(input_y0))
  input_y1 = tf.where(output_y_mask, input_y1, -tf.ones_like(input_y1))
  # (batch_size, output_w)
  input_x0 = tf.where(output_x_mask, input_x0, -tf.ones_like(input_x0))
  input_x1 = tf.where(output_x_mask, input_x1, -tf.ones_like(input_x1))

  input_h = tf.cast(input_h, tf.int32)
  input_w = tf.cast(input_w, tf.int32)
  if images.dtype not in {tf.float32, tf.bfloat16, tf.float16}:
    images = tf.cast(images, tf.float32)
  if images_rank > 3:
    # Reshapes the images since _gather_rows_from_matrix only takes 2-D tensor.
    # (batch_size, input_h, input_w * extra_dims_product)
    images = tf.reshape(images, [-1, input_h, input_w * extra_dims_product])

  # Fetches the rows from the input source images.
  # (batch_size, output_h, input_w * extra_dims_product)
  val_y0 = tf.map_fn(
      lambda x: _gather_rows_from_matrix(x[0], x[1]),
      elems=(images, input_y0),
      fn_output_signature=images.dtype,
      parallel_iterations=32,
  )
  val_y1 = tf.map_fn(
      lambda x: _gather_rows_from_matrix(x[0], x[1]),
      elems=(images, input_y1),
      fn_output_signature=images.dtype,
      parallel_iterations=32,
  )

  if images_rank > 3:
    new_shape = [-1, output_h, input_w] + extra_dims
    # (batch_size, output_h, input_w, ...)
    val_y0 = tf.reshape(val_y0, new_shape)
    val_y1 = tf.reshape(val_y1, new_shape)

  # Transposes the tensors for reusing _gather_rows_from_matrix later.
  new_perm = [0, 2, 1] + extra_dims_perm
  # (batch_size, input_w, output_h, ...)
  val_y0 = tf.transpose(val_y0, new_perm)
  val_y1 = tf.transpose(val_y1, new_perm)

  if images_rank > 3:
    new_shape = [-1, input_w, output_h * extra_dims_product]
    # (batch_size, input_w, output_h * extra_dims_product)
    val_y0 = tf.reshape(val_y0, new_shape)
    val_y1 = tf.reshape(val_y1, new_shape)

  # Fetches the pixels from the rows using the column indices.
  # val_00, val_01, val_10, val_11 store the pixels of the four nearest
  # neighbors of the input source position.
  # (batch_size, output_w, output_h * extra_dims_product)
  val_00 = tf.map_fn(
      lambda x: _gather_rows_from_matrix(x[0], x[1]),
      elems=(val_y0, input_x0),
      fn_output_signature=images.dtype,
      parallel_iterations=32,
  )
  val_01 = tf.map_fn(
      lambda x: _gather_rows_from_matrix(x[0], x[1]),
      elems=(val_y0, input_x1),
      fn_output_signature=images.dtype,
      parallel_iterations=32,
  )
  val_10 = tf.map_fn(
      lambda x: _gather_rows_from_matrix(x[0], x[1]),
      elems=(val_y1, input_x0),
      fn_output_signature=images.dtype,
      parallel_iterations=32,
  )
  val_11 = tf.map_fn(
      lambda x: _gather_rows_from_matrix(x[0], x[1]),
      elems=(val_y1, input_x1),
      fn_output_signature=images.dtype,
      parallel_iterations=32,
  )

  if images_rank > 3:
    new_shape = [-1, output_w, output_h] + extra_dims
    # (batch_size, output_w, output_h, ...)
    val_00 = tf.reshape(val_00, new_shape)
    val_01 = tf.reshape(val_01, new_shape)
    val_10 = tf.reshape(val_10, new_shape)
    val_11 = tf.reshape(val_11, new_shape)

  # (..., batch_size, output_h, output_w)
  new_perm = extra_dims_perm + [0, 2, 1]
  val_00 = tf.transpose(val_00, new_perm)
  val_01 = tf.transpose(val_01, new_perm)
  val_10 = tf.transpose(val_10, new_perm)
  val_11 = tf.transpose(val_11, new_perm)

  # (batch_size, output_height, 1)
  input_y_pos = tf.cast(input_y_pos[:, :, tf.newaxis], images.dtype)
  input_y0 = tf.cast(input_y0[:, :, tf.newaxis], images.dtype)
  input_y1 = tf.cast(input_y1[:, :, tf.newaxis], images.dtype)
  # (batch_size, 1, output_width)
  input_x_pos = tf.cast(input_x_pos[:, tf.newaxis, :], images.dtype)
  input_x0 = tf.cast(input_x0[:, tf.newaxis, :], images.dtype)
  input_x1 = tf.cast(input_x1[:, tf.newaxis, :], images.dtype)

  # Compute the weights of the four nearest neighbors for interpolation.
  # (batch_size, output_height, output_width)
  weight_00 = (input_y1 - input_y_pos) * (input_x1 - input_x_pos)
  weight_01 = (input_y1 - input_y_pos) * (input_x_pos - input_x0)
  weight_10 = (input_y_pos - input_y0) * (input_x1 - input_x_pos)
  weight_11 = (input_y_pos - input_y0) * (input_x_pos - input_x0)

  # (..., batch_size, output_height, output_width)
  output_images = (
      val_00 * weight_00 + val_01 * weight_01 + val_10 * weight_10 +
      val_11 * weight_11)

  # (batch_size, output_height, output_width, ...)
  return tf.transpose(output_images, np.roll(rank_range, -len(extra_dims)))
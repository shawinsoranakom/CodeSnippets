def preprocess_for_train(image,
                         height,
                         width,
                         bbox,
                         fast_mode=True,
                         scope=None,
                         add_image_summaries=True,
                         random_crop=True,
                         use_grayscale=False):
  """Distort one image for training a network.

  Distorting images provides a useful technique for augmenting the data
  set during training in order to make the network invariant to aspects
  of the image that do not effect the label.

  Additionally it would create image_summaries to display the different
  transformations applied to the image.

  Args:
    image: 3-D Tensor of image. If dtype is tf.float32 then the range should be
      [0, 1], otherwise it would converted to tf.float32 assuming that the range
      is [0, MAX], where MAX is largest positive representable number for
      int(8/16/32) data type (see `tf.image.convert_image_dtype` for details).
    height: integer
    width: integer
    bbox: 3-D float Tensor of bounding boxes arranged [1, num_boxes, coords]
      where each coordinate is [0, 1) and the coordinates are arranged
      as [ymin, xmin, ymax, xmax].
    fast_mode: Optional boolean, if True avoids slower transformations (i.e.
      bi-cubic resizing, random_hue or random_contrast).
    scope: Optional scope for name_scope.
    add_image_summaries: Enable image summaries.
    random_crop: Enable random cropping of images during preprocessing for
      training.
    use_grayscale: Whether to convert the image from RGB to grayscale.
  Returns:
    3-D float Tensor of distorted image used for training with range [-1, 1].
  """
  with tf.name_scope(scope, 'distort_image', [image, height, width, bbox]):
    if bbox is None:
      bbox = tf.constant([0.0, 0.0, 1.0, 1.0],
                         dtype=tf.float32,
                         shape=[1, 1, 4])
    if image.dtype != tf.float32:
      image = tf.image.convert_image_dtype(image, dtype=tf.float32)
    # Each bounding box has shape [1, num_boxes, box coords] and
    # the coordinates are ordered [ymin, xmin, ymax, xmax].
    image_with_box = tf.image.draw_bounding_boxes(tf.expand_dims(image, 0),
                                                  bbox)
    if add_image_summaries:
      tf.summary.image('image_with_bounding_boxes', image_with_box)

    if not random_crop:
      distorted_image = image
    else:
      distorted_image, distorted_bbox = distorted_bounding_box_crop(image, bbox)
      # Restore the shape since the dynamic slice based upon the bbox_size loses
      # the third dimension.
      distorted_image.set_shape([None, None, 3])
      image_with_distorted_box = tf.image.draw_bounding_boxes(
          tf.expand_dims(image, 0), distorted_bbox)
      if add_image_summaries:
        tf.summary.image('images_with_distorted_bounding_box',
                         image_with_distorted_box)

    # This resizing operation may distort the images because the aspect
    # ratio is not respected. We select a resize method in a round robin
    # fashion based on the thread number.
    # Note that ResizeMethod contains 4 enumerated resizing methods.

    # We select only 1 case for fast_mode bilinear.
    num_resize_cases = 1 if fast_mode else 4
    distorted_image = apply_with_random_selector(
        distorted_image,
        lambda x, method: tf.image.resize_images(x, [height, width], method),
        num_cases=num_resize_cases)

    if add_image_summaries:
      tf.summary.image(('cropped_' if random_crop else '') + 'resized_image',
                       tf.expand_dims(distorted_image, 0))

    # Randomly flip the image horizontally.
    distorted_image = tf.image.random_flip_left_right(distorted_image)

    # Randomly distort the colors. There are 1 or 4 ways to do it.
    num_distort_cases = 1 if fast_mode else 4
    distorted_image = apply_with_random_selector(
        distorted_image,
        lambda x, ordering: distort_color(x, ordering, fast_mode),
        num_cases=num_distort_cases)

    if use_grayscale:
      distorted_image = tf.image.rgb_to_grayscale(distorted_image)

    if add_image_summaries:
      tf.summary.image('final_distorted_image',
                       tf.expand_dims(distorted_image, 0))
    distorted_image = tf.subtract(distorted_image, 0.5)
    distorted_image = tf.multiply(distorted_image, 2.0)
    return distorted_image
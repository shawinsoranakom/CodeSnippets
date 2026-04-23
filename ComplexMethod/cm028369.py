def preprocess_image(image, augment=False, central_crop_size=None,
                     num_towers=4):
  """Normalizes image to have values in a narrow range around zero.

  Args:
    image: a [H x W x 3] uint8 tensor.
    augment: optional, if True do random image distortion.
    central_crop_size: A tuple (crop_width, crop_height).
    num_towers: optional, number of shots of the same image in the input image.

  Returns:
    A float32 tensor of shape [H x W x 3] with RGB values in the required
    range.
  """
  with tf.compat.v1.variable_scope('PreprocessImage'):
    image = tf.image.convert_image_dtype(image, dtype=tf.float32)
    if augment or central_crop_size:
      if num_towers == 1:
        images = [image]
      else:
        images = tf.split(value=image, num_or_size_splits=num_towers, axis=1)
      if central_crop_size:
        view_crop_size = (int(central_crop_size[0] / num_towers),
                          central_crop_size[1])
        images = [central_crop(img, view_crop_size) for img in images]
      if augment:
        images = [augment_image(img) for img in images]
      image = tf.concat(images, 1)

  return image
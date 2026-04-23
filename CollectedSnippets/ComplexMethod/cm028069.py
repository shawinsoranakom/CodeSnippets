def ResizeImage(image, config, resize_factor=1.0):
  """Resizes image according to config.

  Args:
    image: Uint8 array with shape (height, width, 3).
    config: DelfConfig proto containing the model configuration.
    resize_factor: Optional float resize factor for the input image. If given,
      the maximum and minimum allowed image sizes in `config` are scaled by this
      factor. Must be non-negative.

  Returns:
    resized_image: Uint8 array with resized image.
    scale_factors: 2D float array, with factors used for resizing along height
      and width (If upscaling, larger than 1; if downscaling, smaller than 1).

  Raises:
    ValueError: If `image` has incorrect number of dimensions/channels.
  """
  if resize_factor < 0.0:
    raise ValueError('negative resize_factor is not allowed: %f' %
                     resize_factor)
  if image.ndim != 3:
    raise ValueError('image has incorrect number of dimensions: %d' %
                     image.ndims)
  height, width, channels = image.shape

  # Take into account resize factor.
  max_image_size = resize_factor * config.max_image_size
  min_image_size = resize_factor * config.min_image_size

  if channels != 3:
    raise ValueError('image has incorrect number of channels: %d' % channels)

  largest_side = max(width, height)

  if max_image_size >= 0 and largest_side > max_image_size:
    scale_factor = max_image_size / largest_side
  elif min_image_size >= 0 and largest_side < min_image_size:
    scale_factor = min_image_size / largest_side
  elif config.use_square_images and (height != width):
    scale_factor = 1.0
  else:
    # No resizing needed, early return.
    return image, np.ones(2, dtype=float)

  # Note that new_shape is in (width, height) format (PIL convention), while
  # scale_factors are in (height, width) convention (NumPy convention).
  if config.use_square_images:
    new_shape = (int(round(largest_side * scale_factor)),
                 int(round(largest_side * scale_factor)))
  else:
    new_shape = (int(round(width * scale_factor)),
                 int(round(height * scale_factor)))

  scale_factors = np.array([new_shape[1] / height, new_shape[0] / width],
                           dtype=float)

  pil_image = Image.fromarray(image)
  resized_image = np.array(pil_image.resize(new_shape, resample=Image.BILINEAR))

  return resized_image, scale_factors
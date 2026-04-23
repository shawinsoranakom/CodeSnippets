def preprocess(tensor_dict,
               preprocess_options,
               func_arg_map=None,
               preprocess_vars_cache=None):
  """Preprocess images and bounding boxes.

  Various types of preprocessing (to be implemented) based on the
  preprocess_options dictionary e.g. "crop image" (affects image and possibly
  boxes), "white balance image" (affects only image), etc. If self._options
  is None, no preprocessing is done.

  Args:
    tensor_dict: dictionary that contains images, boxes, and can contain other
                 things as well.
                 images-> rank 4 float32 tensor contains
                          1 image -> [1, height, width, 3].
                          with pixel values varying between [0, 1]
                 boxes-> rank 2 float32 tensor containing
                         the bounding boxes -> [N, 4].
                         Boxes are in normalized form meaning
                         their coordinates vary between [0, 1].
                         Each row is in the form
                         of [ymin, xmin, ymax, xmax].
    preprocess_options: It is a list of tuples, where each tuple contains a
                        function and a dictionary that contains arguments and
                        their values.
    func_arg_map: mapping from preprocessing functions to arguments that they
                  expect to receive and return.
    preprocess_vars_cache: PreprocessorCache object that records previously
                           performed augmentations. Updated in-place. If this
                           function is called multiple times with the same
                           non-null cache, it will perform deterministically.

  Returns:
    tensor_dict: which contains the preprocessed images, bounding boxes, etc.

  Raises:
    ValueError: (a) If the functions passed to Preprocess
                    are not in func_arg_map.
                (b) If the arguments that a function needs
                    do not exist in tensor_dict.
                (c) If image in tensor_dict is not rank 4
  """
  if func_arg_map is None:
    func_arg_map = get_default_func_arg_map()
  # changes the images to image (rank 4 to rank 3) since the functions
  # receive rank 3 tensor for image
  if fields.InputDataFields.image in tensor_dict:
    images = tensor_dict[fields.InputDataFields.image]
    if len(images.get_shape()) != 4:
      raise ValueError('images in tensor_dict should be rank 4')
    image = tf.squeeze(images, axis=0)
    tensor_dict[fields.InputDataFields.image] = image

  # Preprocess inputs based on preprocess_options
  for option in preprocess_options:
    func, params = option
    if func not in func_arg_map:
      raise ValueError('The function %s does not exist in func_arg_map' %
                       (func.__name__))
    arg_names = func_arg_map[func]
    for a in arg_names:
      if a is not None and a not in tensor_dict:
        raise ValueError('The function %s requires argument %s' %
                         (func.__name__, a))

    def get_arg(key):
      return tensor_dict[key] if key is not None else None

    args = [get_arg(a) for a in arg_names]
    if preprocess_vars_cache is not None:
      if six.PY2:
        # pylint: disable=deprecated-method
        arg_spec = inspect.getargspec(func)
        # pylint: enable=deprecated-method
      else:
        arg_spec = inspect.getfullargspec(func)
      if 'preprocess_vars_cache' in arg_spec.args:
        params['preprocess_vars_cache'] = preprocess_vars_cache

    results = func(*args, **params)
    if not isinstance(results, (list, tuple)):
      results = (results,)
    # Removes None args since the return values will not contain those.
    arg_names = [arg_name for arg_name in arg_names if arg_name is not None]
    for res, arg_name in zip(results, arg_names):
      tensor_dict[arg_name] = res

  # changes the image to images (rank 3 to rank 4) to be compatible to what
  # we received in the first place
  if fields.InputDataFields.image in tensor_dict:
    image = tensor_dict[fields.InputDataFields.image]
    images = tf.expand_dims(image, 0)
    tensor_dict[fields.InputDataFields.image] = images

  return tensor_dict
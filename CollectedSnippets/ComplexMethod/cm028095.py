def _ReadAggregatedDescriptors(input_dir, image_list, config):
  """Reads aggregated descriptors.

  Args:
    input_dir: Directory where aggregated descriptors are located.
    image_list: List of image names for which to load descriptors.
    config: AggregationConfig used for images.

  Returns:
    aggregated_descriptors: List containing #images items, each a 1D NumPy
      array.
    visual_words: If using VLAD aggregation, returns an empty list. Otherwise,
      returns a list containing #images items, each a 1D NumPy array.
  """
  # Compose extension of aggregated descriptors.
  extension = '.'
  if config.use_regional_aggregation:
    extension += 'r'
  if config.aggregation_type == _VLAD:
    extension += _VLAD_EXTENSION_SUFFIX
  elif config.aggregation_type == _ASMK:
    extension += _ASMK_EXTENSION_SUFFIX
  elif config.aggregation_type == _ASMK_STAR:
    extension += _ASMK_STAR_EXTENSION_SUFFIX
  else:
    raise ValueError('Invalid aggregation type: %d' % config.aggregation_type)

  num_images = len(image_list)
  aggregated_descriptors = []
  visual_words = []
  print('Starting to collect descriptors for %d images...' % num_images)
  start = time.clock()
  for i in range(num_images):
    if i > 0 and i % _STATUS_CHECK_LOAD_ITERATIONS == 0:
      elapsed = (time.clock() - start)
      print('Reading descriptors for image %d out of %d, last %d '
            'images took %f seconds' %
            (i, num_images, _STATUS_CHECK_LOAD_ITERATIONS, elapsed))
      start = time.clock()

    descriptors_filename = image_list[i] + extension
    descriptors_fullpath = os.path.join(input_dir, descriptors_filename)
    if config.aggregation_type == _VLAD:
      aggregated_descriptors.append(datum_io.ReadFromFile(descriptors_fullpath))
    else:
      d, v = datum_io.ReadPairFromFile(descriptors_fullpath)
      if config.aggregation_type == _ASMK_STAR:
        d = d.astype('uint8')

      aggregated_descriptors.append(d)
      visual_words.append(v)

  return aggregated_descriptors, visual_words
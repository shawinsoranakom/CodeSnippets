def main(argv):
  if len(argv) > 1:
    raise RuntimeError('Too many command-line arguments.')

  # Read list of images.
  print('Reading list of images...')
  image_paths = _ReadImageList(FLAGS.list_images_path)
  num_images = len(image_paths)
  print(f'done! Found {num_images} images')

  # Load images in memory.
  print('Loading images, %d times per image...' % FLAGS.repeat_per_image)
  im_array = []
  for filename in image_paths:
    im = np.array(utils.RgbLoader(filename))
    for _ in range(FLAGS.repeat_per_image):
      im_array.append(im)
  np.random.shuffle(im_array)
  print('done!')

  # Parse DelfConfig proto.
  config = delf_config_pb2.DelfConfig()
  with tf.io.gfile.GFile(FLAGS.delf_config_path, 'r') as f:
    text_format.Parse(f.read(), config)

  extractor_fn = extractor.MakeExtractor(config)

  start = time.time()
  for i, im in enumerate(im_array):
    if i == 0:
      print('Starting to extract DELF features from images...')
    elif i % _STATUS_CHECK_ITERATIONS == 0:
      elapsed = (time.time() - start)
      print(f'Processing image {i} out of {len(im_array)}, last '
            f'{_STATUS_CHECK_ITERATIONS} images took {elapsed} seconds,'
            f'ie {elapsed/_STATUS_CHECK_ITERATIONS} secs/image.')
      start = time.time()

    # Extract and save features.
    extracted_features = extractor_fn(im)

    # Binarize local features, if desired (and if there are local features).
    if (config.use_local_features and FLAGS.binary_local_features and
        extracted_features['local_features']['attention'].size):
      packed_descriptors = np.packbits(
          extracted_features['local_features']['descriptors'] > 0, axis=1)
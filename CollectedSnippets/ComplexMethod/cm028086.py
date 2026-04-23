def main(argv):
  if len(argv) > 1:
    raise RuntimeError('Too many command-line arguments.')

  # Read list of images from dataset file.
  print('Reading list of images from dataset file...')
  query_list, index_list, ground_truth = dataset.ReadDatasetFile(
      FLAGS.dataset_file_path)
  if FLAGS.image_set == 'query':
    image_list = query_list
  else:
    image_list = index_list
  num_images = len(image_list)
  print('done! Found %d images' % num_images)

  # Parse DelfConfig proto.
  config = delf_config_pb2.DelfConfig()
  with tf.io.gfile.GFile(FLAGS.delf_config_path, 'r') as f:
    text_format.Parse(f.read(), config)

  # Create output directory if necessary.
  if not tf.io.gfile.exists(FLAGS.output_features_dir):
    tf.io.gfile.makedirs(FLAGS.output_features_dir)

  extractor_fn = extractor.MakeExtractor(config)

  start = time.time()
  for i in range(num_images):
    if i == 0:
      print('Starting to extract features...')
    elif i % _STATUS_CHECK_ITERATIONS == 0:
      elapsed = (time.time() - start)
      print('Processing image %d out of %d, last %d '
            'images took %f seconds' %
            (i, num_images, _STATUS_CHECK_ITERATIONS, elapsed))
      start = time.time()

    image_name = image_list[i]
    input_image_filename = os.path.join(FLAGS.images_dir,
                                        image_name + _IMAGE_EXTENSION)

    # Compose output file name and decide if image should be skipped.
    should_skip_global = True
    should_skip_local = True
    if config.use_global_features:
      output_global_feature_filename = os.path.join(
          FLAGS.output_features_dir, image_name + _DELG_GLOBAL_EXTENSION)
      if not tf.io.gfile.exists(output_global_feature_filename):
        should_skip_global = False
    if config.use_local_features:
      output_local_feature_filename = os.path.join(
          FLAGS.output_features_dir, image_name + _DELG_LOCAL_EXTENSION)
      if not tf.io.gfile.exists(output_local_feature_filename):
        should_skip_local = False
    if should_skip_global and should_skip_local:
      print('Skipping %s' % image_name)
      continue

    pil_im = utils.RgbLoader(input_image_filename)
    resize_factor = 1.0
    if FLAGS.image_set == 'query':
      # Crop query image according to bounding box.
      original_image_size = max(pil_im.size)
      bbox = [int(round(b)) for b in ground_truth[i]['bbx']]
      pil_im = pil_im.crop(bbox)
      cropped_image_size = max(pil_im.size)
      resize_factor = cropped_image_size / original_image_size

    im = np.array(pil_im)

    # Extract and save features.
    extracted_features = extractor_fn(im, resize_factor)
    if config.use_global_features:
      global_descriptor = extracted_features['global_descriptor']
      datum_io.WriteToFile(global_descriptor, output_global_feature_filename)
    if config.use_local_features:
      locations = extracted_features['local_features']['locations']
      descriptors = extracted_features['local_features']['descriptors']
      feature_scales = extracted_features['local_features']['scales']
      attention = extracted_features['local_features']['attention']
      feature_io.WriteToFile(output_local_feature_filename, locations,
                             feature_scales, descriptors, attention)
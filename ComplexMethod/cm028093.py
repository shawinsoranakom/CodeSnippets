def main(argv):
  if len(argv) > 1:
    raise RuntimeError('Too many command-line arguments.')

  # Process output directory.
  if tf.io.gfile.exists(cmd_args.output_cluster_dir):
    raise RuntimeError(
        'output_cluster_dir = %s already exists. This may indicate that a '
        'previous run already wrote checkpoints in this directory, which would '
        'lead to incorrect training. Please re-run this script by specifying an'
        ' inexisting directory.' % cmd_args.output_cluster_dir)
  else:
    tf.io.gfile.makedirs(cmd_args.output_cluster_dir)

  # Read list of index images from dataset file.
  print('Reading list of index images from dataset file...')
  _, index_list, _ = dataset.ReadDatasetFile(cmd_args.dataset_file_path)
  num_images = len(index_list)
  print('done! Found %d images' % num_images)

  # Loop over list of index images and collect DELF features.
  features_for_clustering = []
  start = time.clock()
  print('Starting to collect features from index images...')
  for i in range(num_images):
    if i > 0 and i % _STATUS_CHECK_ITERATIONS == 0:
      elapsed = (time.clock() - start)
      print('Processing index image %d out of %d, last %d '
            'images took %f seconds' %
            (i, num_images, _STATUS_CHECK_ITERATIONS, elapsed))
      start = time.clock()

    features_filename = index_list[i] + _DELF_EXTENSION
    features_fullpath = os.path.join(cmd_args.features_dir, features_filename)
    _, _, features, _, _ = feature_io.ReadFromFile(features_fullpath)
    if features.size != 0:
      assert features.shape[1] == _DELF_DIM
    for feature in features:
      features_for_clustering.append(feature)

  features_for_clustering = np.array(features_for_clustering, dtype=np.float32)
  print('All features were loaded! There are %d features, each with %d '
        'dimensions' %
        (features_for_clustering.shape[0], features_for_clustering.shape[1]))

  # Run K-means clustering.
  def _get_input_fn():
    """Helper function to create input function and hook for training.

    Returns:
      input_fn: Input function for k-means Estimator training.
      init_hook: Hook used to load data during training.
    """
    init_hook = _IteratorInitHook()

    def _input_fn():
      """Produces tf.data.Dataset object for k-means training.

      Returns:
        Tensor with the data for training.
      """
      features_placeholder = tf.compat.v1.placeholder(
          tf.float32, features_for_clustering.shape)
      delf_dataset = tf.data.Dataset.from_tensor_slices((features_placeholder))
      delf_dataset = delf_dataset.shuffle(1000).batch(
          features_for_clustering.shape[0])
      iterator = tf.compat.v1.data.make_initializable_iterator(delf_dataset)

      def _initializer_fn(sess):
        """Initialize dataset iterator, feed in the data."""
        sess.run(
            iterator.initializer,
            feed_dict={features_placeholder: features_for_clustering})

      init_hook.iterator_initializer_fn = _initializer_fn
      return iterator.get_next()

    return _input_fn, init_hook

  input_fn, init_hook = _get_input_fn()

  kmeans = tf.compat.v1.estimator.experimental.KMeans(
      num_clusters=cmd_args.num_clusters,
      model_dir=cmd_args.output_cluster_dir,
      use_mini_batch=False,
  )

  print('Starting K-means clustering...')
  start = time.clock()
  for i in range(cmd_args.num_iterations):
    kmeans.train(input_fn, hooks=[init_hook])
    average_sum_squared_error = kmeans.evaluate(
        input_fn, hooks=[init_hook])['score'] / features_for_clustering.shape[0]
    elapsed = (time.clock() - start)
    print('K-means iteration %d (out of %d) took %f seconds, '
          'average-sum-of-squares: %f' %
          (i, cmd_args.num_iterations, elapsed, average_sum_squared_error))
    start = time.clock()

  print('K-means clustering finished!')
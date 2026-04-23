def test_retrieval(datasets, net, epoch, writer=None, model_directory=None,
                   precompute_whitening=None, data_root='data', multiscale=[1.],
                   test_image_size=1024):
  """Testing step.

  Evaluates the network on the provided test datasets by computing single-scale
  mAP for easy/medium/hard cases. If `writer` is specified, saves the mAP
  values in a tensorboard supported format.

  Args:
    datasets: List of dataset names for model testing (from
      `_TEST_DATASET_NAMES`).
    net: Network to evaluate.
    epoch: Integer, epoch number.
    writer: Tensorboard writer.
    model_directory: String, path to the model directory.
    precompute_whitening: Dataset used to learn whitening. If no
      precomputation required, then `None`. Only 'retrieval-SfM-30k' and
      'retrieval-SfM-120k' datasets are supported for whitening pre-computation.
    data_root: Absolute path to the data folder.
    multiscale: List of scales for multiscale testing.
    test_image_size: Integer, maximum size of the test images.
  """
  global_features_utils.debug_and_log(">> Testing step:")
  global_features_utils.debug_and_log(
          '>> Evaluating network on test datasets...')

  # Precompute whitening.
  if precompute_whitening is not None:

    # If whitening already precomputed, load it and skip the computations.
    filename = os.path.join(
            model_directory, 'learned_whitening_mP_{}_epoch.pkl'.format(epoch))
    filename_layer = os.path.join(
            model_directory,
            'learned_whitening_layer_config_{}_epoch.pkl'.format(
                    epoch))

    if tf.io.gfile.exists(filename):
      global_features_utils.debug_and_log(
              '>> {}: Whitening for this epoch is already precomputed. '
              'Loading...'.format(precompute_whitening))
      with tf.io.gfile.GFile(filename, 'rb') as learned_whitening_file:
        learned_whitening = pickle.load(learned_whitening_file)

    else:
      start = time.time()
      global_features_utils.debug_and_log(
              '>> {}: Learning whitening...'.format(precompute_whitening))

      # Loading db.
      db_root = os.path.join(data_root, 'train', precompute_whitening)
      ims_root = os.path.join(db_root, 'ims')
      db_filename = os.path.join(db_root,
                                 '{}-whiten.pkl'.format(precompute_whitening))
      with tf.io.gfile.GFile(db_filename, 'rb') as f:
        db = pickle.load(f)
      images = [sfm120k.id2filename(db['cids'][i], ims_root) for i in
                range(len(db['cids']))]

      # Extract whitening vectors.
      global_features_utils.debug_and_log(
              '>> {}: Extracting...'.format(precompute_whitening))
      wvecs = global_model.extract_global_descriptors_from_list(net, images,
                                                                test_image_size)

      # Learning whitening.
      global_features_utils.debug_and_log(
              '>> {}: Learning...'.format(precompute_whitening))
      wvecs = wvecs.numpy()
      mean_vector, projection_matrix = whiten.whitenlearn(wvecs, db['qidxs'],
                                                          db['pidxs'])
      learned_whitening = {'m': mean_vector, 'P': projection_matrix}

      global_features_utils.debug_and_log(
              '>> {}: Elapsed time: {}'.format(precompute_whitening,
                                               global_features_utils.htime(
                                                       time.time() - start)))
      # Save learned_whitening parameters for a later use.
      with tf.io.gfile.GFile(filename, 'wb') as learned_whitening_file:
        pickle.dump(learned_whitening, learned_whitening_file)

      # Saving whitening as a layer.
      bias = -np.dot(mean_vector.T, projection_matrix.T)
      whitening_layer = tf.keras.layers.Dense(
              net.meta['outputdim'],
              activation=None,
              use_bias=True,
              kernel_initializer=tf.keras.initializers.Constant(
                      projection_matrix.T),
              bias_initializer=tf.keras.initializers.Constant(bias)
      )
      with tf.io.gfile.GFile(filename_layer, 'wb') as learned_whitening_file:
        pickle.dump(whitening_layer.get_config(), learned_whitening_file)
  else:
    learned_whitening = None

  # Evaluate on test datasets.
  for dataset in datasets:
    start = time.time()

    # Prepare config structure for the test dataset.
    cfg = test_dataset.CreateConfigForTestDataset(dataset,
                                                  os.path.join(data_root))
    images = [cfg['im_fname'](cfg, i) for i in range(cfg['n'])]
    qimages = [cfg['qim_fname'](cfg, i) for i in range(cfg['nq'])]
    bounding_boxes = [tuple(cfg['gnd'][i]['bbx']) for i in range(cfg['nq'])]

    # Extract database and query vectors.
    global_features_utils.debug_and_log(
            '>> {}: Extracting database images...'.format(dataset))
    vecs = global_model.extract_global_descriptors_from_list(
            net, images, test_image_size, scales=multiscale)
    global_features_utils.debug_and_log(
            '>> {}: Extracting query images...'.format(dataset))
    qvecs = global_model.extract_global_descriptors_from_list(
            net, qimages, test_image_size, bounding_boxes,
            scales=multiscale)

    global_features_utils.debug_and_log('>> {}: Evaluating...'.format(dataset))

    # Convert the obtained descriptors to numpy.
    vecs = vecs.numpy()
    qvecs = qvecs.numpy()

    # Search, rank and print test set metrics.
    _calculate_metrics_and_export_to_tensorboard(vecs, qvecs, dataset, cfg,
                                                 writer, epoch, whiten=False)

    if learned_whitening is not None:
      # Whiten the vectors.
      mean_vector = learned_whitening['m']
      projection_matrix = learned_whitening['P']
      vecs_lw = whiten.whitenapply(vecs, mean_vector, projection_matrix)
      qvecs_lw = whiten.whitenapply(qvecs, mean_vector, projection_matrix)

      # Search, rank, and print.
      _calculate_metrics_and_export_to_tensorboard(
              vecs_lw, qvecs_lw, dataset, cfg, writer, epoch, whiten=True)

    global_features_utils.debug_and_log(
            '>> {}: Elapsed time: {}'.format(
                    dataset, global_features_utils.htime(time.time() - start)))
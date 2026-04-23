def main(argv):
  if len(argv) > 1:
    raise RuntimeError('Too many command-line arguments.')

  # Parse dataset to obtain query/index images, and ground-truth.
  print('Parsing dataset...')
  query_list, index_list, ground_truth = dataset.ReadDatasetFile(
      FLAGS.dataset_file_path)
  num_query_images = len(query_list)
  num_index_images = len(index_list)
  (_, medium_ground_truth,
   hard_ground_truth) = dataset.ParseEasyMediumHardGroundTruth(ground_truth)
  print('done! Found %d queries and %d index images' %
        (num_query_images, num_index_images))

  # Read global features.
  query_global_features = _ReadDelgGlobalDescriptors(FLAGS.query_features_dir,
                                                     query_list)
  index_global_features = _ReadDelgGlobalDescriptors(FLAGS.index_features_dir,
                                                     index_list)

  # Compute similarity between query and index images, potentially re-ranking
  # with geometric verification.
  ranks_before_gv = np.zeros([num_query_images, num_index_images],
                             dtype='int32')
  if FLAGS.use_geometric_verification:
    medium_ranks_after_gv = np.zeros([num_query_images, num_index_images],
                                     dtype='int32')
    hard_ranks_after_gv = np.zeros([num_query_images, num_index_images],
                                   dtype='int32')
  for i in range(num_query_images):
    print('Performing retrieval with query %d (%s)...' % (i, query_list[i]))
    start = time.time()

    # Compute similarity between global descriptors.
    similarities = np.dot(index_global_features, query_global_features[i])
    ranks_before_gv[i] = np.argsort(-similarities)

    # Re-rank using geometric verification.
    if FLAGS.use_geometric_verification:
      medium_ranks_after_gv[i] = image_reranking.RerankByGeometricVerification(
          input_ranks=ranks_before_gv[i],
          initial_scores=similarities,
          query_name=query_list[i],
          index_names=index_list,
          query_features_dir=FLAGS.query_features_dir,
          index_features_dir=FLAGS.index_features_dir,
          junk_ids=set(medium_ground_truth[i]['junk']),
          local_feature_extension=_DELG_LOCAL_EXTENSION,
          ransac_seed=0,
          descriptor_matching_threshold=FLAGS
          .local_descriptor_matching_threshold,
          ransac_residual_threshold=FLAGS.ransac_residual_threshold,
          use_ratio_test=FLAGS.use_ratio_test)
      hard_ranks_after_gv[i] = image_reranking.RerankByGeometricVerification(
          input_ranks=ranks_before_gv[i],
          initial_scores=similarities,
          query_name=query_list[i],
          index_names=index_list,
          query_features_dir=FLAGS.query_features_dir,
          index_features_dir=FLAGS.index_features_dir,
          junk_ids=set(hard_ground_truth[i]['junk']),
          local_feature_extension=_DELG_LOCAL_EXTENSION,
          ransac_seed=0,
          descriptor_matching_threshold=FLAGS
          .local_descriptor_matching_threshold,
          ransac_residual_threshold=FLAGS.ransac_residual_threshold,
          use_ratio_test=FLAGS.use_ratio_test)

    elapsed = (time.time() - start)
    print('done! Retrieval for query %d took %f seconds' % (i, elapsed))

  # Create output directory if necessary.
  if not tf.io.gfile.exists(FLAGS.output_dir):
    tf.io.gfile.makedirs(FLAGS.output_dir)

  # Compute metrics.
  medium_metrics = dataset.ComputeMetrics(ranks_before_gv, medium_ground_truth,
                                          _PR_RANKS)
  hard_metrics = dataset.ComputeMetrics(ranks_before_gv, hard_ground_truth,
                                        _PR_RANKS)
  if FLAGS.use_geometric_verification:
    medium_metrics_after_gv = dataset.ComputeMetrics(medium_ranks_after_gv,
                                                     medium_ground_truth,
                                                     _PR_RANKS)
    hard_metrics_after_gv = dataset.ComputeMetrics(hard_ranks_after_gv,
                                                   hard_ground_truth, _PR_RANKS)

  # Write metrics to file.
  mean_average_precision_dict = {
      'medium': medium_metrics[0],
      'hard': hard_metrics[0]
  }
  mean_precisions_dict = {'medium': medium_metrics[1], 'hard': hard_metrics[1]}
  mean_recalls_dict = {'medium': medium_metrics[2], 'hard': hard_metrics[2]}
  if FLAGS.use_geometric_verification:
    mean_average_precision_dict.update({
        'medium_after_gv': medium_metrics_after_gv[0],
        'hard_after_gv': hard_metrics_after_gv[0]
    })
    mean_precisions_dict.update({
        'medium_after_gv': medium_metrics_after_gv[1],
        'hard_after_gv': hard_metrics_after_gv[1]
    })
    mean_recalls_dict.update({
        'medium_after_gv': medium_metrics_after_gv[2],
        'hard_after_gv': hard_metrics_after_gv[2]
    })
  dataset.SaveMetricsFile(mean_average_precision_dict, mean_precisions_dict,
                          mean_recalls_dict, _PR_RANKS,
                          os.path.join(FLAGS.output_dir, _METRICS_FILENAME))
def main(argv):
  if len(argv) > 1:
    raise RuntimeError('Too many command-line arguments.')

  # Parse dataset to obtain query/index images, and ground-truth.
  print('Parsing dataset...')
  query_list, index_list, ground_truth = dataset.ReadDatasetFile(
      cmd_args.dataset_file_path)
  num_query_images = len(query_list)
  num_index_images = len(index_list)
  (_, medium_ground_truth,
   hard_ground_truth) = dataset.ParseEasyMediumHardGroundTruth(ground_truth)
  print('done! Found %d queries and %d index images' %
        (num_query_images, num_index_images))

  # Parse AggregationConfig protos.
  query_config = aggregation_config_pb2.AggregationConfig()
  with tf.io.gfile.GFile(cmd_args.query_aggregation_config_path, 'r') as f:
    text_format.Merge(f.read(), query_config)
  index_config = aggregation_config_pb2.AggregationConfig()
  with tf.io.gfile.GFile(cmd_args.index_aggregation_config_path, 'r') as f:
    text_format.Merge(f.read(), index_config)

  # Read aggregated descriptors.
  query_aggregated_descriptors, query_visual_words = _ReadAggregatedDescriptors(
      cmd_args.query_aggregation_dir, query_list, query_config)
  index_aggregated_descriptors, index_visual_words = _ReadAggregatedDescriptors(
      cmd_args.index_aggregation_dir, index_list, index_config)

  # Create similarity computer.
  similarity_computer = (
      feature_aggregation_similarity.SimilarityAggregatedRepresentation(
          index_config))

  # Compute similarity between query and index images, potentially re-ranking
  # with geometric verification.
  ranks_before_gv = np.zeros([num_query_images, num_index_images],
                             dtype='int32')
  if cmd_args.use_geometric_verification:
    medium_ranks_after_gv = np.zeros([num_query_images, num_index_images],
                                     dtype='int32')
    hard_ranks_after_gv = np.zeros([num_query_images, num_index_images],
                                   dtype='int32')
  for i in range(num_query_images):
    print('Performing retrieval with query %d (%s)...' % (i, query_list[i]))
    start = time.clock()

    # Compute similarity between aggregated descriptors.
    similarities = np.zeros([num_index_images])
    for j in range(num_index_images):
      similarities[j] = similarity_computer.ComputeSimilarity(
          query_aggregated_descriptors[i], index_aggregated_descriptors[j],
          query_visual_words[i], index_visual_words[j])

    ranks_before_gv[i] = np.argsort(-similarities)

    # Re-rank using geometric verification.
    if cmd_args.use_geometric_verification:
      medium_ranks_after_gv[i] = image_reranking.RerankByGeometricVerification(
          ranks_before_gv[i], similarities, query_list[i], index_list,
          cmd_args.query_features_dir, cmd_args.index_features_dir,
          set(medium_ground_truth[i]['junk']))
      hard_ranks_after_gv[i] = image_reranking.RerankByGeometricVerification(
          ranks_before_gv[i], similarities, query_list[i], index_list,
          cmd_args.query_features_dir, cmd_args.index_features_dir,
          set(hard_ground_truth[i]['junk']))

    elapsed = (time.clock() - start)
    print('done! Retrieval for query %d took %f seconds' % (i, elapsed))

  # Create output directory if necessary.
  if not tf.io.gfile.exists(cmd_args.output_dir):
    tf.io.gfile.makedirs(cmd_args.output_dir)

  # Compute metrics.
  medium_metrics = dataset.ComputeMetrics(ranks_before_gv, medium_ground_truth,
                                          _PR_RANKS)
  hard_metrics = dataset.ComputeMetrics(ranks_before_gv, hard_ground_truth,
                                        _PR_RANKS)
  if cmd_args.use_geometric_verification:
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
  if cmd_args.use_geometric_verification:
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
                          os.path.join(cmd_args.output_dir, _METRICS_FILENAME))
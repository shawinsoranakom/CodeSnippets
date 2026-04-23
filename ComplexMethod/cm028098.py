def RerankByGeometricVerification(input_ranks,
                                  initial_scores,
                                  query_name,
                                  index_names,
                                  query_features_dir,
                                  index_features_dir,
                                  junk_ids,
                                  local_feature_extension=_DELF_EXTENSION,
                                  ransac_seed=None,
                                  descriptor_matching_threshold=0.9,
                                  ransac_residual_threshold=10.0,
                                  use_ratio_test=False):
  """Re-ranks retrieval results using geometric verification.

  Args:
    input_ranks: 1D NumPy array with indices of top-ranked index images, sorted
      from the most to the least similar.
    initial_scores: 1D NumPy array with initial similarity scores between query
      and index images. Entry i corresponds to score for image i.
    query_name: Name for query image (string).
    index_names: List of names for index images (strings).
    query_features_dir: Directory where query local feature file is located
      (string).
    index_features_dir: Directory where index local feature files are located
      (string).
    junk_ids: Set with indices of junk images which should not be considered
      during re-ranking.
    local_feature_extension: String, extension to use for loading local feature
      files.
    ransac_seed: Seed used by RANSAC. If None (default), no seed is provided.
    descriptor_matching_threshold: Threshold used for local descriptor matching.
    ransac_residual_threshold: Residual error threshold for considering matches
      as inliers, used in RANSAC algorithm.
    use_ratio_test: If True, descriptor matching is performed via ratio test,
      instead of distance-based threshold.

  Returns:
    output_ranks: 1D NumPy array with index image indices, sorted from the most
      to the least similar according to the geometric verification and initial
      scores.

  Raises:
    ValueError: If `input_ranks`, `initial_scores` and `index_names` do not have
      the same number of entries.
  """
  num_index_images = len(index_names)
  if len(input_ranks) != num_index_images:
    raise ValueError('input_ranks and index_names have different number of '
                     'elements: %d vs %d' %
                     (len(input_ranks), len(index_names)))
  if len(initial_scores) != num_index_images:
    raise ValueError('initial_scores and index_names have different number of '
                     'elements: %d vs %d' %
                     (len(initial_scores), len(index_names)))

  # Filter out junk images from list that will be re-ranked.
  input_ranks_for_gv = []
  for ind in input_ranks:
    if ind not in junk_ids:
      input_ranks_for_gv.append(ind)
  num_to_rerank = min(_NUM_TO_RERANK, len(input_ranks_for_gv))

  # Load query image features.
  query_features_path = os.path.join(query_features_dir,
                                     query_name + local_feature_extension)
  query_locations, _, query_descriptors, _, _ = feature_io.ReadFromFile(
      query_features_path)

  # Initialize list containing number of inliers and initial similarity scores.
  inliers_and_initial_scores = []
  for i in range(num_index_images):
    inliers_and_initial_scores.append([0, initial_scores[i]])

  # Loop over top-ranked images and get results.
  print('Starting to re-rank')
  for i in range(num_to_rerank):
    if i > 0 and i % _STATUS_CHECK_GV_ITERATIONS == 0:
      print('Re-ranking: i = %d out of %d' % (i, num_to_rerank))

    index_image_id = input_ranks_for_gv[i]

    # Load index image features.
    index_image_features_path = os.path.join(
        index_features_dir,
        index_names[index_image_id] + local_feature_extension)
    (index_image_locations, _, index_image_descriptors, _,
     _) = feature_io.ReadFromFile(index_image_features_path)

    inliers_and_initial_scores[index_image_id][0], _ = MatchFeatures(
        query_locations,
        query_descriptors,
        index_image_locations,
        index_image_descriptors,
        ransac_seed=ransac_seed,
        descriptor_matching_threshold=descriptor_matching_threshold,
        ransac_residual_threshold=ransac_residual_threshold,
        use_ratio_test=use_ratio_test)

  # Sort based on (inliers_score, initial_score).
  def _InliersInitialScoresSorting(k):
    """Helper function to sort list based on two entries.

    Args:
      k: Index into `inliers_and_initial_scores`.

    Returns:
      Tuple containing inlier score and initial score.
    """
    return (inliers_and_initial_scores[k][0], inliers_and_initial_scores[k][1])

  output_ranks = sorted(
      range(num_index_images), key=_InliersInitialScoresSorting, reverse=True)

  return output_ranks
def MatchFeatures(query_locations,
                  query_descriptors,
                  index_image_locations,
                  index_image_descriptors,
                  ransac_seed=None,
                  descriptor_matching_threshold=0.9,
                  ransac_residual_threshold=10.0,
                  query_im_array=None,
                  index_im_array=None,
                  query_im_scale_factors=None,
                  index_im_scale_factors=None,
                  use_ratio_test=False):
  """Matches local features using geometric verification.

  First, finds putative local feature matches by matching `query_descriptors`
  against a KD-tree from the `index_image_descriptors`. Then, attempts to fit an
  affine transformation between the putative feature corresponces using their
  locations.

  Args:
    query_locations: Locations of local features for query image. NumPy array of
      shape [#query_features, 2].
    query_descriptors: Descriptors of local features for query image. NumPy
      array of shape [#query_features, depth].
    index_image_locations: Locations of local features for index image. NumPy
      array of shape [#index_image_features, 2].
    index_image_descriptors: Descriptors of local features for index image.
      NumPy array of shape [#index_image_features, depth].
    ransac_seed: Seed used by RANSAC. If None (default), no seed is provided.
    descriptor_matching_threshold: Threshold below which a pair of local
      descriptors is considered a potential match, and will be fed into RANSAC.
      If use_ratio_test==False, this is a simple distance threshold. If
      use_ratio_test==True, this is Lowe's ratio test threshold.
    ransac_residual_threshold: Residual error threshold for considering matches
      as inliers, used in RANSAC algorithm.
    query_im_array: Optional. If not None, contains a NumPy array with the query
      image, used to produce match visualization, if there is a match.
    index_im_array: Optional. Same as `query_im_array`, but for index image.
    query_im_scale_factors: Optional. If not None, contains a NumPy array with
      the query image scales, used to produce match visualization, if there is a
      match. If None and a visualization will be produced, [1.0, 1.0] is used
      (ie, feature locations are not scaled).
    index_im_scale_factors: Optional. Same as `query_im_scale_factors`, but for
      index image.
    use_ratio_test: If True, descriptor matching is performed via ratio test,
      instead of distance-based threshold.

  Returns:
    score: Number of inliers of match. If no match is found, returns 0.
    match_viz_bytes: Encoded image bytes with visualization of the match, if
      there is one, and if `query_im_array` and `index_im_array` are properly
      set. Otherwise, it's an empty bytes string.

  Raises:
    ValueError: If local descriptors from query and index images have different
      dimensionalities.
  """
  num_features_query = query_locations.shape[0]
  num_features_index_image = index_image_locations.shape[0]
  if not num_features_query or not num_features_index_image:
    return 0, b''

  local_feature_dim = query_descriptors.shape[1]
  if index_image_descriptors.shape[1] != local_feature_dim:
    raise ValueError(
        'Local feature dimensionality is not consistent for query and index '
        'images.')

  # Construct KD-tree used to find nearest neighbors.
  index_image_tree = spatial.cKDTree(index_image_descriptors)
  if use_ratio_test:
    distances, indices = index_image_tree.query(
        query_descriptors, k=2, n_jobs=-1)
    query_locations_to_use = np.array([
        query_locations[i,]
        for i in range(num_features_query)
        if distances[i][0] < descriptor_matching_threshold * distances[i][1]
    ])
    index_image_locations_to_use = np.array([
        index_image_locations[indices[i][0],]
        for i in range(num_features_query)
        if distances[i][0] < descriptor_matching_threshold * distances[i][1]
    ])
  else:
    _, indices = index_image_tree.query(
        query_descriptors,
        distance_upper_bound=descriptor_matching_threshold,
        n_jobs=-1)

    # Select feature locations for putative matches.
    query_locations_to_use = np.array([
        query_locations[i,]
        for i in range(num_features_query)
        if indices[i] != num_features_index_image
    ])
    index_image_locations_to_use = np.array([
        index_image_locations[indices[i],]
        for i in range(num_features_query)
        if indices[i] != num_features_index_image
    ])

  # If there are not enough putative matches, early return 0.
  if query_locations_to_use.shape[0] <= _MIN_RANSAC_SAMPLES:
    return 0, b''

  # Perform geometric verification using RANSAC.
  _, inliers = measure.ransac(
      (index_image_locations_to_use, query_locations_to_use),
      transform.AffineTransform,
      min_samples=_MIN_RANSAC_SAMPLES,
      residual_threshold=ransac_residual_threshold,
      max_trials=_NUM_RANSAC_TRIALS,
      random_state=ransac_seed)
  match_viz_bytes = b''

  if inliers is None:
    inliers = []
  elif query_im_array is not None and index_im_array is not None:
    if query_im_scale_factors is None:
      query_im_scale_factors = [1.0, 1.0]
    if index_im_scale_factors is None:
      index_im_scale_factors = [1.0, 1.0]
    inlier_idxs = np.nonzero(inliers)[0]
    _, ax = plt.subplots()
    ax.axis('off')
    ax.xaxis.set_major_locator(plt.NullLocator())
    ax.yaxis.set_major_locator(plt.NullLocator())
    plt.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)
    plt.margins(0, 0)
    feature.plot_matches(
        ax,
        query_im_array,
        index_im_array,
        query_locations_to_use * query_im_scale_factors,
        index_image_locations_to_use * index_im_scale_factors,
        np.column_stack((inlier_idxs, inlier_idxs)),
        only_matches=True)

    match_viz_io = io.BytesIO()
    plt.savefig(match_viz_io, format='jpeg', bbox_inches='tight', pad_inches=0)
    match_viz_bytes = match_viz_io.getvalue()

  return sum(inliers), match_viz_bytes
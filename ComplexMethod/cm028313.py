def refine_keypoints(regressed_keypoints,
                     keypoint_candidates,
                     keypoint_scores,
                     num_keypoint_candidates,
                     bboxes=None,
                     unmatched_keypoint_score=0.1,
                     box_scale=1.2,
                     candidate_search_scale=0.3,
                     candidate_ranking_mode='min_distance',
                     score_distance_offset=1e-6,
                     keypoint_depth_candidates=None,
                     keypoint_score_threshold=0.1,
                     score_distance_multiplier=0.1,
                     keypoint_std_dev=None):
  """Refines regressed keypoints by snapping to the nearest candidate keypoints.

  The initial regressed keypoints represent a full set of keypoints regressed
  from the centers of the objects. The keypoint candidates are estimated
  independently from heatmaps, and are not associated with any object instances.
  This function refines the regressed keypoints by "snapping" to the
  nearest/highest score/highest score-distance ratio (depending on the
  candidate_ranking_mode) candidate of the same keypoint type (e.g. "nose").
  If no candidates are nearby, the regressed keypoint remains unchanged.

  In order to snap a regressed keypoint to a candidate keypoint, the following
  must be satisfied:
  - the candidate keypoint must be of the same type as the regressed keypoint
  - the candidate keypoint must not lie outside the predicted boxes (or the
    boxes which encloses the regressed keypoints for the instance if `bboxes` is
    not provided). Note that the box is scaled by
    `regressed_box_scale` in height and width, to provide some margin around the
    keypoints
  - the distance to the closest candidate keypoint cannot exceed
    candidate_search_scale * max(height, width), where height and width refer to
    the bounding box for the instance.

  Note that the same candidate keypoint is allowed to snap to regressed
  keypoints in difference instances.

  Args:
    regressed_keypoints: A float tensor of shape
      [batch_size, num_instances, num_keypoints, 2] with the initial regressed
      keypoints.
    keypoint_candidates: A tensor of shape
      [batch_size, max_candidates, num_keypoints, 2] holding the location of
      keypoint candidates in [y, x] format (expressed in absolute coordinates in
      the output coordinate frame).
    keypoint_scores: A float tensor of shape
      [batch_size, max_candidates, num_keypoints] indicating the scores for
      keypoint candidates.
    num_keypoint_candidates: An integer tensor of shape
      [batch_size, num_keypoints] indicating the number of valid candidates for
      each keypoint type, as there may be padding (dim 1) of
      `keypoint_candidates` and `keypoint_scores`.
    bboxes: A tensor of shape [batch_size, num_instances, 4] with predicted
      bounding boxes for each instance, expressed in the output coordinate
      frame. If not provided, boxes will be computed from regressed keypoints.
    unmatched_keypoint_score: float, the default score to use for regressed
      keypoints that are not successfully snapped to a nearby candidate.
    box_scale: float, the multiplier to expand the bounding boxes (either the
      provided boxes or those which tightly cover the regressed keypoints) for
      an instance. This scale is typically larger than 1.0 when not providing
      `bboxes`.
    candidate_search_scale: float, the scale parameter that multiplies the
      largest dimension of a bounding box. The resulting distance becomes a
      search radius for candidates in the vicinity of each regressed keypoint.
    candidate_ranking_mode: A string as one of ['min_distance',
      'score_distance_ratio', 'score_scaled_distance_ratio',
      'gaussian_weighted'] indicating how to select the candidate. If invalid
      value is provided, an ValueError will be raised.
    score_distance_offset: The distance offset to apply in the denominator when
      candidate_ranking_mode is 'score_distance_ratio'. The metric to maximize
      in this scenario is score / (distance + score_distance_offset). Larger
      values of score_distance_offset make the keypoint score gain more relative
      importance.
    keypoint_depth_candidates: (optional) A float tensor of shape
      [batch_size, max_candidates, num_keypoints] indicating the depths for
      keypoint candidates.
    keypoint_score_threshold: float, The heatmap score threshold for
      a keypoint to become a valid candidate.
    score_distance_multiplier: A scalar used to multiply the bounding box size
      to be the offset in the score-to-distance-ratio formula.
    keypoint_std_dev: A list of float represent the standard deviation of the
      Gaussian kernel used to rank the keypoint candidates. It offers the
      flexibility of using different sizes of Gaussian kernel for each keypoint
      class. Only applicable when the candidate_ranking_mode equals to
      'gaussian_weighted'.

  Returns:
    A tuple with:
    refined_keypoints: A float tensor of shape
      [batch_size, num_instances, num_keypoints, 2] with the final, refined
      keypoints.
    refined_scores: A float tensor of shape
      [batch_size, num_instances, num_keypoints] with scores associated with all
      instances and keypoints in `refined_keypoints`.

  Raises:
    ValueError: if provided candidate_ranking_mode is not one of
      ['min_distance', 'score_distance_ratio']
  """
  batch_size, num_instances, num_keypoints, _ = (
      shape_utils.combined_static_and_dynamic_shape(regressed_keypoints))
  max_candidates = keypoint_candidates.shape[1]

  # Replace all invalid (i.e. padded) keypoint candidates with NaN.
  # This will prevent them from being considered.
  range_tiled = tf.tile(
      tf.reshape(tf.range(max_candidates), [1, max_candidates, 1]),
      [batch_size, 1, num_keypoints])
  num_candidates_tiled = tf.tile(tf.expand_dims(num_keypoint_candidates, 1),
                                 [1, max_candidates, 1])
  invalid_candidates = range_tiled >= num_candidates_tiled

  # Pairwise squared distances between regressed keypoints and candidate
  # keypoints (for a single keypoint type).
  # Shape [batch_size, num_instances, 1, num_keypoints, 2].
  regressed_keypoint_expanded = tf.expand_dims(regressed_keypoints,
                                               axis=2)
  # Shape [batch_size, 1, max_candidates, num_keypoints, 2].
  keypoint_candidates_expanded = tf.expand_dims(
      keypoint_candidates, axis=1)
  # Use explicit tensor shape broadcasting (since the tensor dimensions are
  # expanded to 5D) to make it tf.lite compatible.
  regressed_keypoint_expanded = tf.tile(
      regressed_keypoint_expanded, multiples=[1, 1, max_candidates, 1, 1])
  keypoint_candidates_expanded = tf.tile(
      keypoint_candidates_expanded, multiples=[1, num_instances, 1, 1, 1])
  # Replace tf.math.squared_difference by "-" operator and tf.multiply ops since
  # tf.lite convert doesn't support squared_difference with undetermined
  # dimension.
  diff = regressed_keypoint_expanded - keypoint_candidates_expanded
  sqrd_distances = tf.math.reduce_sum(tf.multiply(diff, diff), axis=-1)
  distances = tf.math.sqrt(sqrd_distances)

  # Replace the invalid candidated with large constant (10^5) to make sure the
  # following reduce_min/argmin behaves properly.
  max_dist = 1e5
  distances = tf.where(
      tf.tile(
          tf.expand_dims(invalid_candidates, axis=1),
          multiples=[1, num_instances, 1, 1]),
      tf.ones_like(distances) * max_dist,
      distances
  )

  # Determine the candidates that have the minimum distance to the regressed
  # keypoints. Shape [batch_size, num_instances, num_keypoints].
  min_distances = tf.math.reduce_min(distances, axis=2)
  if candidate_ranking_mode == 'min_distance':
    nearby_candidate_inds = tf.math.argmin(distances, axis=2)
  elif candidate_ranking_mode == 'score_distance_ratio':
    # tiled_keypoint_scores:
    # Shape [batch_size, num_instances, max_candidates, num_keypoints].
    tiled_keypoint_scores = tf.tile(
        tf.expand_dims(keypoint_scores, axis=1),
        multiples=[1, num_instances, 1, 1],
    )
    ranking_scores = tiled_keypoint_scores / (distances + score_distance_offset)
    nearby_candidate_inds = tf.math.argmax(
        ranking_scores, axis=2, output_type=tf.int32
    )
  elif candidate_ranking_mode == 'score_scaled_distance_ratio':
    ranking_scores = sdr_scaled_ranking_score(
        keypoint_scores, distances, bboxes, score_distance_multiplier
    )
    nearby_candidate_inds = tf.math.argmax(
        ranking_scores, axis=2, output_type=tf.int32
    )
  elif candidate_ranking_mode == 'gaussian_weighted':
    ranking_scores = gaussian_weighted_score(
        keypoint_scores, distances, keypoint_std_dev, bboxes
    )
    nearby_candidate_inds = tf.math.argmax(
        ranking_scores, axis=2, output_type=tf.int32
    )
    weighted_scores = tf.math.reduce_max(ranking_scores, axis=2)
  else:
    raise ValueError(
        'Not recognized candidate_ranking_mode: %s' % candidate_ranking_mode
    )

  # Gather the coordinates and scores corresponding to the closest candidates.
  # Shape of tensors are [batch_size, num_instances, num_keypoints, 2] and
  # [batch_size, num_instances, num_keypoints], respectively.
  (nearby_candidate_coords, nearby_candidate_scores,
   nearby_candidate_depths) = (
       _gather_candidates_at_indices(keypoint_candidates, keypoint_scores,
                                     nearby_candidate_inds,
                                     keypoint_depth_candidates))

  # If the ranking mode is 'gaussian_weighted', we use the ranking scores as the
  # final keypoint confidence since their values are in between [0, 1].
  if candidate_ranking_mode == 'gaussian_weighted':
    nearby_candidate_scores = weighted_scores

  if bboxes is None:
    # Filter out the chosen candidate with score lower than unmatched
    # keypoint score.
    mask = tf.cast(nearby_candidate_scores <
                   keypoint_score_threshold, tf.int32)
  else:
    bboxes_flattened = tf.reshape(bboxes, [-1, 4])

    # Scale the bounding boxes.
    # Shape [batch_size, num_instances, 4].
    boxlist = box_list.BoxList(bboxes_flattened)
    boxlist_scaled = box_list_ops.scale_height_width(
        boxlist, box_scale, box_scale)
    bboxes_scaled = boxlist_scaled.get()
    bboxes = tf.reshape(bboxes_scaled, [batch_size, num_instances, 4])

    # Get ymin, xmin, ymax, xmax bounding box coordinates, tiled per keypoint.
    # Shape [batch_size, num_instances, num_keypoints].
    bboxes_tiled = tf.tile(tf.expand_dims(bboxes, 2), [1, 1, num_keypoints, 1])
    ymin, xmin, ymax, xmax = tf.unstack(bboxes_tiled, axis=3)

    # Produce a mask that indicates whether the original regressed keypoint
    # should be used instead of a candidate keypoint.
    # Shape [batch_size, num_instances, num_keypoints].
    search_radius = (
        tf.math.maximum(ymax - ymin, xmax - xmin) * candidate_search_scale)
    mask = (tf.cast(nearby_candidate_coords[:, :, :, 0] < ymin, tf.int32) +
            tf.cast(nearby_candidate_coords[:, :, :, 0] > ymax, tf.int32) +
            tf.cast(nearby_candidate_coords[:, :, :, 1] < xmin, tf.int32) +
            tf.cast(nearby_candidate_coords[:, :, :, 1] > xmax, tf.int32) +
            # Filter out the chosen candidate with score lower than unmatched
            # keypoint score.
            tf.cast(nearby_candidate_scores <
                    keypoint_score_threshold, tf.int32) +
            tf.cast(min_distances > search_radius, tf.int32))
  mask = mask > 0

  # Create refined keypoints where candidate keypoints replace original
  # regressed keypoints if they are in the vicinity of the regressed keypoints.
  # Shape [batch_size, num_instances, num_keypoints, 2].
  refined_keypoints = tf.where(
      tf.tile(tf.expand_dims(mask, -1), [1, 1, 1, 2]),
      regressed_keypoints,
      nearby_candidate_coords)

  # Update keypoints scores. In the case where we use the original regressed
  # keypoints, we use a default score of `unmatched_keypoint_score`.
  # Shape [batch_size, num_instances, num_keypoints].
  refined_scores = tf.where(
      mask,
      unmatched_keypoint_score * tf.ones_like(nearby_candidate_scores),
      nearby_candidate_scores)

  refined_depths = None
  if nearby_candidate_depths is not None:
    refined_depths = tf.where(mask, tf.zeros_like(nearby_candidate_depths),
                              nearby_candidate_depths)

  return refined_keypoints, refined_scores, refined_depths
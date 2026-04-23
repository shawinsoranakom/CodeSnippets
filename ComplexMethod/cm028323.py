def _summarize_target_assignment(self, groundtruth_boxes_list, match_list):
    """Creates tensorflow summaries for the input boxes and anchors.

    This function creates four summaries corresponding to the average
    number (over images in a batch) of (1) groundtruth boxes, (2) anchors
    marked as positive, (3) anchors marked as negative, and (4) anchors marked
    as ignored.

    Args:
      groundtruth_boxes_list: a list of 2-D tensors of shape [num_boxes, 4]
        containing corners of the groundtruth boxes.
      match_list: a list of matcher.Match objects encoding the match between
        anchors and groundtruth boxes for each image of the batch,
        with rows of the Match objects corresponding to groundtruth boxes
        and columns corresponding to anchors.
    """
    # TODO(rathodv): Add a test for these summaries.
    try:
      # TODO(kaftan): Integrate these summaries into the v2 style loops
      with tf.compat.v2.init_scope():
        if tf.compat.v2.executing_eagerly():
          return
    except AttributeError:
      pass

    avg_num_gt_boxes = tf.reduce_mean(
        tf.cast(
            tf.stack([tf.shape(x)[0] for x in groundtruth_boxes_list]),
            dtype=tf.float32))
    avg_num_matched_gt_boxes = tf.reduce_mean(
        tf.cast(
            tf.stack([match.num_matched_rows() for match in match_list]),
            dtype=tf.float32))
    avg_pos_anchors = tf.reduce_mean(
        tf.cast(
            tf.stack([match.num_matched_columns() for match in match_list]),
            dtype=tf.float32))
    avg_neg_anchors = tf.reduce_mean(
        tf.cast(
            tf.stack([match.num_unmatched_columns() for match in match_list]),
            dtype=tf.float32))
    avg_ignored_anchors = tf.reduce_mean(
        tf.cast(
            tf.stack([match.num_ignored_columns() for match in match_list]),
            dtype=tf.float32))

    tf.summary.scalar('AvgNumGroundtruthBoxesPerImage',
                      avg_num_gt_boxes,
                      family='TargetAssignment')
    tf.summary.scalar('AvgNumGroundtruthBoxesMatchedPerImage',
                      avg_num_matched_gt_boxes,
                      family='TargetAssignment')
    tf.summary.scalar('AvgNumPositiveAnchorsPerImage',
                      avg_pos_anchors,
                      family='TargetAssignment')
    tf.summary.scalar('AvgNumNegativeAnchorsPerImage',
                      avg_neg_anchors,
                      family='TargetAssignment')
    tf.summary.scalar('AvgNumIgnoredAnchorsPerImage',
                      avg_ignored_anchors,
                      family='TargetAssignment')
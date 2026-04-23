def extract_images_and_targets(read_data):
    """Extract images and targets from the input dict."""
    image = read_data[fields.InputDataFields.image]
    key = ''
    if fields.InputDataFields.source_id in read_data:
      key = read_data[fields.InputDataFields.source_id]
    location_gt = read_data[fields.InputDataFields.groundtruth_boxes]
    classes_gt = tf.cast(read_data[fields.InputDataFields.groundtruth_classes],
                         tf.int32)
    classes_gt -= label_id_offset

    if merge_multiple_label_boxes and use_multiclass_scores:
      raise ValueError(
          'Using both merge_multiple_label_boxes and use_multiclass_scores is'
          'not supported'
      )

    if merge_multiple_label_boxes:
      location_gt, classes_gt, _ = util_ops.merge_boxes_with_multiple_labels(
          location_gt, classes_gt, num_classes)
      classes_gt = tf.cast(classes_gt, tf.float32)
    elif use_multiclass_scores:
      classes_gt = tf.cast(read_data[fields.InputDataFields.multiclass_scores],
                           tf.float32)
    else:
      classes_gt = util_ops.padded_one_hot_encoding(
          indices=classes_gt, depth=num_classes, left_pad=0)
    masks_gt = read_data.get(fields.InputDataFields.groundtruth_instance_masks)
    keypoints_gt = read_data.get(fields.InputDataFields.groundtruth_keypoints)
    if (merge_multiple_label_boxes and (
        masks_gt is not None or keypoints_gt is not None)):
      raise NotImplementedError('Multi-label support is only for boxes.')
    weights_gt = read_data.get(
        fields.InputDataFields.groundtruth_weights)
    return (image, key, location_gt, classes_gt, masks_gt, keypoints_gt,
            weights_gt)
def ExportSegmentsToCOCO(image_ids,
                         detection_masks,
                         detection_scores,
                         detection_classes,
                         categories,
                         output_path=None):
  """Export segmentation masks in numpy arrays to COCO API.

  This function converts a set of predicted instance masks represented
  as numpy arrays to dictionaries that can be ingested by the COCO API.
  Inputs to this function are lists, consisting of segments, scores and
  classes, respectively, corresponding to each image for which detections
  have been produced.

  Note this function is recommended to use for small dataset.
  For large dataset, it should be used with a merge function
  (e.g. in map reduce), otherwise the memory consumption is large.

  We assume that for each image, masks, scores and classes are in
  correspondence --- that is: detection_masks[i, :, :, :], detection_scores[i]
  and detection_classes[i] are associated with the same detection.

  Args:
    image_ids: list of image ids (typically ints or strings)
    detection_masks: list of numpy arrays with shape [num_detection, h, w, 1]
      and type uint8. The height and width should match the shape of
      corresponding image.
    detection_scores: list of numpy arrays (float) with shape
      [num_detection]. Note that num_detection can be different
      for each entry in the list.
    detection_classes: list of numpy arrays (int) with shape
      [num_detection]. Note that num_detection can be different
      for each entry in the list.
    categories: a list of dictionaries representing all possible categories.
      Each dict in this list must have an integer 'id' key uniquely identifying
      this category.
    output_path: (optional) path for exporting result to JSON

  Returns:
    list of dictionaries that can be read by COCO API, where each entry
    corresponds to a single detection and has keys from:
    ['image_id', 'category_id', 'segmentation', 'score'].

  Raises:
    ValueError: if detection_masks and detection_classes do not have the
      right lengths or if each of the elements inside these lists do not
      have the correct shapes.
  """
  if not (len(image_ids) == len(detection_masks) == len(detection_scores) ==
          len(detection_classes)):
    raise ValueError('Input lists must have the same length')

  segment_export_list = []
  for image_id, masks, scores, classes in zip(image_ids, detection_masks,
                                              detection_scores,
                                              detection_classes):

    if len(classes.shape) != 1 or len(scores.shape) != 1:
      raise ValueError('All entries in detection_classes and detection_scores'
                       'expected to be of rank 1.')
    if len(masks.shape) != 4:
      raise ValueError('All entries in masks expected to be of '
                       'rank 4. Given {}'.format(masks.shape))

    num_boxes = classes.shape[0]
    if not num_boxes == masks.shape[0] == scores.shape[0]:
      raise ValueError('Corresponding entries in segment_classes, '
                       'detection_scores and detection_boxes should have '
                       'compatible shapes (i.e., agree on the 0th dimension).')

    category_id_set = set([cat['id'] for cat in categories])
    segment_export_list.extend(ExportSingleImageDetectionMasksToCoco(
        image_id, category_id_set, np.squeeze(masks, axis=3), scores, classes))

  if output_path:
    with tf.gfile.GFile(output_path, 'w') as fid:
      json_utils.Dump(segment_export_list, fid, float_digits=4, indent=2)
  return segment_export_list
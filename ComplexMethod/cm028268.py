def ExportKeypointsToCOCO(image_ids,
                          detection_keypoints,
                          detection_scores,
                          detection_classes,
                          categories,
                          output_path=None):
  """Exports keypoints in numpy arrays to COCO API.

  This function converts a set of predicted keypoints represented
  as numpy arrays to dictionaries that can be ingested by the COCO API.
  Inputs to this function are lists, consisting of keypoints, scores and
  classes, respectively, corresponding to each image for which detections
  have been produced.

  We assume that for each image, keypoints, scores and classes are in
  correspondence --- that is: detection_keypoints[i, :, :, :],
  detection_scores[i] and detection_classes[i] are associated with the same
  detection.

  Args:
    image_ids: list of image ids (typically ints or strings)
    detection_keypoints: list of numpy arrays with shape
      [num_detection, num_keypoints, 2] and type float32 in absolute
      x-y coordinates.
    detection_scores: list of numpy arrays (float) with shape
      [num_detection]. Note that num_detection can be different
      for each entry in the list.
    detection_classes: list of numpy arrays (int) with shape
      [num_detection]. Note that num_detection can be different
      for each entry in the list.
    categories: a list of dictionaries representing all possible categories.
      Each dict in this list must have an integer 'id' key uniquely identifying
      this category and an integer 'num_keypoints' key specifying the number of
      keypoints the category has.
    output_path: (optional) path for exporting result to JSON

  Returns:
    list of dictionaries that can be read by COCO API, where each entry
    corresponds to a single detection and has keys from:
    ['image_id', 'category_id', 'keypoints', 'score'].

  Raises:
    ValueError: if detection_keypoints and detection_classes do not have the
      right lengths or if each of the elements inside these lists do not
      have the correct shapes.
  """
  if not (len(image_ids) == len(detection_keypoints) ==
          len(detection_scores) == len(detection_classes)):
    raise ValueError('Input lists must have the same length')

  keypoints_export_list = []
  for image_id, keypoints, scores, classes in zip(
      image_ids, detection_keypoints, detection_scores, detection_classes):

    if len(classes.shape) != 1 or len(scores.shape) != 1:
      raise ValueError('All entries in detection_classes and detection_scores'
                       'expected to be of rank 1.')
    if len(keypoints.shape) != 3:
      raise ValueError('All entries in keypoints expected to be of '
                       'rank 3. Given {}'.format(keypoints.shape))

    num_boxes = classes.shape[0]
    if not num_boxes == keypoints.shape[0] == scores.shape[0]:
      raise ValueError('Corresponding entries in detection_classes, '
                       'detection_keypoints, and detection_scores should have '
                       'compatible shapes (i.e., agree on the 0th dimension).')

    category_id_set = set([cat['id'] for cat in categories])
    category_id_to_num_keypoints_map = {
        cat['id']: cat['num_keypoints'] for cat in categories
        if 'num_keypoints' in cat}

    for i in range(num_boxes):
      if classes[i] not in category_id_set:
        raise ValueError('class id should be in category_id_set\n')

      if classes[i] in category_id_to_num_keypoints_map:
        num_keypoints = category_id_to_num_keypoints_map[classes[i]]
        # Adds extra ones to indicate the visibility for each keypoint as is
        # recommended by MSCOCO.
        instance_keypoints = np.concatenate(
            [keypoints[i, 0:num_keypoints, :],
             np.expand_dims(np.ones(num_keypoints), axis=1)],
            axis=1).astype(int)

        instance_keypoints = instance_keypoints.flatten().tolist()
        keypoints_export_list.append({
            'image_id': image_id,
            'category_id': int(classes[i]),
            'keypoints': instance_keypoints,
            'score': float(scores[i])
        })

  if output_path:
    with tf.gfile.GFile(output_path, 'w') as fid:
      json_utils.Dump(keypoints_export_list, fid, float_digits=4, indent=2)
  return keypoints_export_list
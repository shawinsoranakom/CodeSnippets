def make_sequence_example(dataset_name,
                          video_id,
                          encoded_images,
                          image_height,
                          image_width,
                          image_format=None,
                          image_source_ids=None,
                          timestamps=None,
                          is_annotated=None,
                          bboxes=None,
                          label_strings=None,
                          detection_bboxes=None,
                          detection_classes=None,
                          detection_scores=None,
                          use_strs_for_source_id=False,
                          context_features=None,
                          context_feature_length=None,
                          context_features_image_id_list=None):
  """Constructs tf.SequenceExamples.

  Args:
    dataset_name: String with dataset name.
    video_id: String with video id.
    encoded_images: A [num_frames] list (or numpy array) of encoded image
      frames.
    image_height: Height of the images.
    image_width: Width of the images.
    image_format: Format of encoded images.
    image_source_ids: (Optional) A [num_frames] list of unique string ids for
      each image.
    timestamps: (Optional) A [num_frames] list (or numpy array) array with image
      timestamps.
    is_annotated: (Optional) A [num_frames] list (or numpy array) array
      in which each element indicates whether the frame has been annotated
      (1) or not (0).
    bboxes: (Optional) A list (with num_frames elements) of [num_boxes_i, 4]
      numpy float32 arrays holding boxes for each frame.
    label_strings: (Optional) A list (with num_frames_elements) of [num_boxes_i]
      numpy string arrays holding object string labels for each frame.
    detection_bboxes: (Optional) A list (with num_frames elements) of
      [num_boxes_i, 4] numpy float32 arrays holding prediction boxes for each
      frame.
    detection_classes: (Optional) A list (with num_frames_elements) of
      [num_boxes_i] numpy int64 arrays holding predicted classes for each frame.
    detection_scores: (Optional) A list (with num_frames_elements) of
      [num_boxes_i] numpy float32 arrays holding predicted object scores for
      each frame.
    use_strs_for_source_id: (Optional) Whether to write the source IDs as
      strings rather than byte lists of characters.
    context_features: (Optional) A list or numpy array of features to use in
      Context R-CNN, of length num_context_features * context_feature_length.
    context_feature_length: (Optional) The length of each context feature, used
      for reshaping.
    context_features_image_id_list: (Optional) A list of image ids of length
      num_context_features corresponding to the context features.

  Returns:
    A tf.train.SequenceExample.
  """
  num_frames = len(encoded_images)
  image_encoded = np.expand_dims(encoded_images, axis=-1)
  if timestamps is None:
    timestamps = np.arange(num_frames)
  image_timestamps = np.expand_dims(timestamps, axis=-1)

  # Context fields.
  context_dict = {
      'example/dataset_name': context_bytes_feature([dataset_name]),
      'clip/start/timestamp': context_int64_feature([image_timestamps[0][0]]),
      'clip/end/timestamp': context_int64_feature([image_timestamps[-1][0]]),
      'clip/frames': context_int64_feature([num_frames]),
      'image/channels': context_int64_feature([3]),
      'image/height': context_int64_feature([image_height]),
      'image/width': context_int64_feature([image_width]),
      'clip/media_id': context_bytes_feature([video_id])
  }

  # Sequence fields.
  feature_list = {
      'image/encoded': sequence_bytes_feature(image_encoded),
      'image/timestamp': sequence_int64_feature(image_timestamps),
  }

  # Add optional fields.
  if image_format is not None:
    context_dict['image/format'] = context_bytes_feature([image_format])
  if image_source_ids is not None:
    if use_strs_for_source_id:
      feature_list['image/source_id'] = sequence_strings_feature(
          image_source_ids)
    else:
      feature_list['image/source_id'] = sequence_bytes_feature(image_source_ids)
  if bboxes is not None:
    bbox_ymin, bbox_xmin, bbox_ymax, bbox_xmax = boxes_to_box_components(bboxes)
    feature_list['region/bbox/xmin'] = sequence_float_feature(bbox_xmin)
    feature_list['region/bbox/xmax'] = sequence_float_feature(bbox_xmax)
    feature_list['region/bbox/ymin'] = sequence_float_feature(bbox_ymin)
    feature_list['region/bbox/ymax'] = sequence_float_feature(bbox_ymax)
    if is_annotated is None:
      is_annotated = np.ones(num_frames, dtype=np.int64)
    is_annotated = np.expand_dims(is_annotated, axis=-1)
    feature_list['region/is_annotated'] = sequence_int64_feature(is_annotated)

  if label_strings is not None:
    feature_list['region/label/string'] = sequence_bytes_feature(
        label_strings)

  if detection_bboxes is not None:
    det_bbox_ymin, det_bbox_xmin, det_bbox_ymax, det_bbox_xmax = (
        boxes_to_box_components(detection_bboxes))
    feature_list['predicted/region/bbox/xmin'] = sequence_float_feature(
        det_bbox_xmin)
    feature_list['predicted/region/bbox/xmax'] = sequence_float_feature(
        det_bbox_xmax)
    feature_list['predicted/region/bbox/ymin'] = sequence_float_feature(
        det_bbox_ymin)
    feature_list['predicted/region/bbox/ymax'] = sequence_float_feature(
        det_bbox_ymax)
  if detection_classes is not None:
    feature_list['predicted/region/label/index'] = sequence_int64_feature(
        detection_classes)
  if detection_scores is not None:
    feature_list['predicted/region/label/confidence'] = sequence_float_feature(
        detection_scores)

  if context_features is not None:
    context_dict['image/context_features'] = context_float_feature(
        context_features)
  if context_feature_length is not None:
    context_dict['image/context_feature_length'] = context_int64_feature(
        context_feature_length)
  if context_features_image_id_list is not None:
    context_dict['image/context_features_image_id_list'] = (
        context_bytes_feature(context_features_image_id_list))

  context = tf.train.Features(feature=context_dict)
  feature_lists = tf.train.FeatureLists(feature_list=feature_list)

  sequence_example = tf.train.SequenceExample(
      context=context,
      feature_lists=feature_lists)
  return sequence_example
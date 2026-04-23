def visualize_detection_results(result_dict,
                                tag,
                                global_step,
                                categories,
                                summary_dir='',
                                export_dir='',
                                agnostic_mode=False,
                                show_groundtruth=False,
                                groundtruth_box_visualization_color='black',
                                min_score_thresh=.5,
                                max_num_predictions=20,
                                skip_scores=False,
                                skip_labels=False,
                                keep_image_id_for_visualization_export=False):
  """Visualizes detection results and writes visualizations to image summaries.

  This function visualizes an image with its detected bounding boxes and writes
  to image summaries which can be viewed on tensorboard.  It optionally also
  writes images to a directory. In the case of missing entry in the label map,
  unknown class name in the visualization is shown as "N/A".

  Args:
    result_dict: a dictionary holding groundtruth and detection
      data corresponding to each image being evaluated.  The following keys
      are required:
        'original_image': a numpy array representing the image with shape
          [1, height, width, 3] or [1, height, width, 1]
        'detection_boxes': a numpy array of shape [N, 4]
        'detection_scores': a numpy array of shape [N]
        'detection_classes': a numpy array of shape [N]
      The following keys are optional:
        'groundtruth_boxes': a numpy array of shape [N, 4]
        'groundtruth_keypoints': a numpy array of shape [N, num_keypoints, 2]
      Detections are assumed to be provided in decreasing order of score and for
      display, and we assume that scores are probabilities between 0 and 1.
    tag: tensorboard tag (string) to associate with image.
    global_step: global step at which the visualization are generated.
    categories: a list of dictionaries representing all possible categories.
      Each dict in this list has the following keys:
          'id': (required) an integer id uniquely identifying this category
          'name': (required) string representing category name
            e.g., 'cat', 'dog', 'pizza'
          'supercategory': (optional) string representing the supercategory
            e.g., 'animal', 'vehicle', 'food', etc
    summary_dir: the output directory to which the image summaries are written.
    export_dir: the output directory to which images are written.  If this is
      empty (default), then images are not exported.
    agnostic_mode: boolean (default: False) controlling whether to evaluate in
      class-agnostic mode or not.
    show_groundtruth: boolean (default: False) controlling whether to show
      groundtruth boxes in addition to detected boxes
    groundtruth_box_visualization_color: box color for visualizing groundtruth
      boxes
    min_score_thresh: minimum score threshold for a box to be visualized
    max_num_predictions: maximum number of detections to visualize
    skip_scores: whether to skip score when drawing a single detection
    skip_labels: whether to skip label when drawing a single detection
    keep_image_id_for_visualization_export: whether to keep image identifier in
      filename when exported to export_dir
  Raises:
    ValueError: if result_dict does not contain the expected keys (i.e.,
      'original_image', 'detection_boxes', 'detection_scores',
      'detection_classes')
  """
  detection_fields = fields.DetectionResultFields
  input_fields = fields.InputDataFields
  if not set([
      input_fields.original_image,
      detection_fields.detection_boxes,
      detection_fields.detection_scores,
      detection_fields.detection_classes,
  ]).issubset(set(result_dict.keys())):
    raise ValueError('result_dict does not contain all expected keys.')
  if show_groundtruth and input_fields.groundtruth_boxes not in result_dict:
    raise ValueError('If show_groundtruth is enabled, result_dict must contain '
                     'groundtruth_boxes.')
  tf.logging.info('Creating detection visualizations.')
  category_index = label_map_util.create_category_index(categories)

  image = np.squeeze(result_dict[input_fields.original_image], axis=0)
  if image.shape[2] == 1:  # If one channel image, repeat in RGB.
    image = np.tile(image, [1, 1, 3])
  detection_boxes = result_dict[detection_fields.detection_boxes]
  detection_scores = result_dict[detection_fields.detection_scores]
  detection_classes = np.int32((result_dict[
      detection_fields.detection_classes]))
  detection_keypoints = result_dict.get(detection_fields.detection_keypoints)
  detection_masks = result_dict.get(detection_fields.detection_masks)
  detection_boundaries = result_dict.get(detection_fields.detection_boundaries)

  # Plot groundtruth underneath detections
  if show_groundtruth:
    groundtruth_boxes = result_dict[input_fields.groundtruth_boxes]
    groundtruth_keypoints = result_dict.get(input_fields.groundtruth_keypoints)
    vis_utils.visualize_boxes_and_labels_on_image_array(
        image=image,
        boxes=groundtruth_boxes,
        classes=None,
        scores=None,
        category_index=category_index,
        keypoints=groundtruth_keypoints,
        use_normalized_coordinates=False,
        max_boxes_to_draw=None,
        groundtruth_box_visualization_color=groundtruth_box_visualization_color)
  vis_utils.visualize_boxes_and_labels_on_image_array(
      image,
      detection_boxes,
      detection_classes,
      detection_scores,
      category_index,
      instance_masks=detection_masks,
      instance_boundaries=detection_boundaries,
      keypoints=detection_keypoints,
      use_normalized_coordinates=False,
      max_boxes_to_draw=max_num_predictions,
      min_score_thresh=min_score_thresh,
      agnostic_mode=agnostic_mode,
      skip_scores=skip_scores,
      skip_labels=skip_labels)

  if export_dir:
    if keep_image_id_for_visualization_export and result_dict[fields.
                                                              InputDataFields()
                                                              .key]:
      export_path = os.path.join(export_dir, 'export-{}-{}.png'.format(
          tag, result_dict[fields.InputDataFields().key]))
    else:
      export_path = os.path.join(export_dir, 'export-{}.png'.format(tag))
    vis_utils.save_image_array_as_png(image, export_path)

  summary = tf.Summary(value=[
      tf.Summary.Value(
          tag=tag,
          image=tf.Summary.Image(
              encoded_image_string=vis_utils.encode_image_array_as_png_str(
                  image)))
  ])
  summary_writer = tf.summary.FileWriterCache.get(summary_dir)
  summary_writer.add_summary(summary, global_step)

  tf.logging.info('Detection visualizations written to summary with tag %s.',
                  tag)
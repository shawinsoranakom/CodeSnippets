def __init__(self,
               annotation_file,
               include_mask,
               include_keypoint=False,
               need_rescale_bboxes=True,
               need_rescale_keypoints=False,
               per_category_metrics=False,
               max_num_eval_detections=100,
               kpt_oks_sigmas=None):
    """Constructs COCO evaluation class.

    The class provides the interface to COCO metrics_fn. The
    _update_op() takes detections from each image and push them to
    self.detections. The _evaluate() loads a JSON file in COCO annotation format
    as the ground-truths and runs COCO evaluation.

    Args:
      annotation_file: a JSON file that stores annotations of the eval dataset.
        If `annotation_file` is None, ground-truth annotations will be loaded
        from the dataloader.
      include_mask: a boolean to indicate whether or not to include the mask
        eval.
      include_keypoint: a boolean to indicate whether or not to include the
        keypoint eval.
      need_rescale_bboxes: If true bboxes in `predictions` will be rescaled back
        to absolute values (`image_info` is needed in this case).
      need_rescale_keypoints: If true keypoints in `predictions` will be
        rescaled back to absolute values (`image_info` is needed in this case).
      per_category_metrics: Whether to return per category metrics.
      max_num_eval_detections: Maximum number of detections to evaluate in coco
        eval api. Default at 100.
      kpt_oks_sigmas: The sigmas used to calculate keypoint OKS. See
        http://cocodataset.org/#keypoints-eval. When None, it will use the
        defaults in COCO.
    Raises:
      ValueError: if max_num_eval_detections is not an integer.
    """
    if annotation_file:
      if annotation_file.startswith('gs://'):
        _, local_val_json = tempfile.mkstemp(suffix='.json')
        tf.io.gfile.remove(local_val_json)

        tf.io.gfile.copy(annotation_file, local_val_json)
        atexit.register(tf.io.gfile.remove, local_val_json)
      else:
        local_val_json = annotation_file
      self._coco_gt = coco_utils.COCOWrapper(
          eval_type=('mask' if include_mask else 'box'),
          annotation_file=local_val_json)
    self._annotation_file = annotation_file
    self._include_mask = include_mask
    self._include_keypoint = include_keypoint
    self._per_category_metrics = per_category_metrics
    if max_num_eval_detections is None or not isinstance(
        max_num_eval_detections, int):
      raise ValueError('max_num_eval_detections must be an integer.')
    self._metric_names = [
        'AP', 'AP50', 'AP75', 'APs', 'APm', 'APl', 'ARmax1', 'ARmax10',
        f'ARmax{max_num_eval_detections}', 'ARs', 'ARm', 'ARl'
    ]
    self.max_num_eval_detections = max_num_eval_detections
    self._required_prediction_fields = [
        'source_id', 'num_detections', 'detection_classes', 'detection_scores',
        'detection_boxes'
    ]
    self._need_rescale_bboxes = need_rescale_bboxes
    self._need_rescale_keypoints = need_rescale_keypoints
    if self._need_rescale_bboxes or self._need_rescale_keypoints:
      self._required_prediction_fields.append('image_info')
    self._required_groundtruth_fields = [
        'source_id', 'height', 'width', 'classes', 'boxes'
    ]
    if self._include_mask:
      mask_metric_names = ['mask_' + x for x in self._metric_names]
      self._metric_names.extend(mask_metric_names)
      self._required_prediction_fields.extend(['detection_masks'])
      self._required_groundtruth_fields.extend(['masks'])
    if self._include_keypoint:
      keypoint_metric_names = [
          'AP', 'AP50', 'AP75', 'APm', 'APl', 'ARmax1', 'ARmax10',
          f'ARmax{max_num_eval_detections}', 'ARm', 'ARl'
      ]
      keypoint_metric_names = ['keypoint_' + x for x in keypoint_metric_names]
      self._metric_names.extend(keypoint_metric_names)
      self._required_prediction_fields.extend(['detection_keypoints'])
      self._required_groundtruth_fields.extend(['keypoints'])
      self._kpt_oks_sigmas = kpt_oks_sigmas

    self.reset_states()
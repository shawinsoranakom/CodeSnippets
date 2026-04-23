def get_evaluators(eval_config, categories, evaluator_options=None):
  """Returns the evaluator class according to eval_config, valid for categories.

  Args:
    eval_config: An `eval_pb2.EvalConfig`.
    categories: A list of dicts, each of which has the following keys -
        'id': (required) an integer id uniquely identifying this category.
        'name': (required) string representing category name e.g., 'cat', 'dog'.
        'keypoints': (optional) dict mapping this category's keypoints to unique
          ids.
    evaluator_options: A dictionary of metric names (see
      EVAL_METRICS_CLASS_DICT) to `DetectionEvaluator` initialization
      keyword arguments. For example:
      evalator_options = {
        'coco_detection_metrics': {'include_metrics_per_category': True}
      }

  Returns:
    An list of instances of DetectionEvaluator.

  Raises:
    ValueError: if metric is not in the metric class dictionary.
  """
  evaluator_options = evaluator_options or {}
  eval_metric_fn_keys = eval_config.metrics_set
  if not eval_metric_fn_keys:
    eval_metric_fn_keys = [EVAL_DEFAULT_METRIC]
  evaluators_list = []
  for eval_metric_fn_key in eval_metric_fn_keys:
    if eval_metric_fn_key not in EVAL_METRICS_CLASS_DICT:
      raise ValueError('Metric not found: {}'.format(eval_metric_fn_key))
    kwargs_dict = (evaluator_options[eval_metric_fn_key] if eval_metric_fn_key
                   in evaluator_options else {})
    evaluators_list.append(EVAL_METRICS_CLASS_DICT[eval_metric_fn_key](
        categories,
        **kwargs_dict))

  if isinstance(eval_config, eval_pb2.EvalConfig):
    parameterized_metrics = eval_config.parameterized_metric
    for parameterized_metric in parameterized_metrics:
      assert parameterized_metric.HasField('parameterized_metric')
      if parameterized_metric.WhichOneof(
          'parameterized_metric') == EVAL_KEYPOINT_METRIC:
        keypoint_metrics = parameterized_metric.coco_keypoint_metrics
        # Create category to keypoints mapping dict.
        category_keypoints = {}
        class_label = keypoint_metrics.class_label
        category = None
        for cat in categories:
          if cat['name'] == class_label:
            category = cat
            break
        if not category:
          continue
        keypoints_for_this_class = category['keypoints']
        category_keypoints = [{
            'id': keypoints_for_this_class[kp_name], 'name': kp_name
        } for kp_name in keypoints_for_this_class]
        # Create keypoint evaluator for this category.
        evaluators_list.append(EVAL_METRICS_CLASS_DICT[EVAL_KEYPOINT_METRIC](
            category['id'], category_keypoints, class_label,
            keypoint_metrics.keypoint_label_to_sigmas))
  return evaluators_list
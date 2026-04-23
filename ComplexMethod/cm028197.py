def evaluator_options_from_eval_config(eval_config):
  """Produces a dictionary of evaluation options for each eval metric.

  Args:
    eval_config: An `eval_pb2.EvalConfig`.

  Returns:
    evaluator_options: A dictionary of metric names (see
      EVAL_METRICS_CLASS_DICT) to `DetectionEvaluator` initialization
      keyword arguments. For example:
      evalator_options = {
        'coco_detection_metrics': {'include_metrics_per_category': True}
      }
  """
  eval_metric_fn_keys = eval_config.metrics_set
  evaluator_options = {}
  for eval_metric_fn_key in eval_metric_fn_keys:
    if eval_metric_fn_key in (
        'coco_detection_metrics', 'coco_mask_metrics', 'lvis_mask_metrics'):
      evaluator_options[eval_metric_fn_key] = {
          'include_metrics_per_category': (
              eval_config.include_metrics_per_category)
      }

      if (hasattr(eval_config, 'all_metrics_per_category') and
          eval_config.all_metrics_per_category):
        evaluator_options[eval_metric_fn_key].update({
            'all_metrics_per_category': eval_config.all_metrics_per_category
        })
      # For coco detection eval, if the eval_config proto contains the
      # "skip_predictions_for_unlabeled_class" field, include this field in
      # evaluator_options.
      if eval_metric_fn_key == 'coco_detection_metrics' and hasattr(
          eval_config, 'skip_predictions_for_unlabeled_class'):
        evaluator_options[eval_metric_fn_key].update({
            'skip_predictions_for_unlabeled_class':
                (eval_config.skip_predictions_for_unlabeled_class)
        })
      for super_category in eval_config.super_categories:
        if 'super_categories' not in evaluator_options[eval_metric_fn_key]:
          evaluator_options[eval_metric_fn_key]['super_categories'] = {}
        key = super_category
        value = eval_config.super_categories[key].split(',')
        evaluator_options[eval_metric_fn_key]['super_categories'][key] = value
      if eval_metric_fn_key == 'lvis_mask_metrics' and hasattr(
          eval_config, 'export_path'):
        evaluator_options[eval_metric_fn_key].update({
            'export_path': eval_config.export_path
        })

    elif eval_metric_fn_key == 'precision_at_recall_detection_metrics':
      evaluator_options[eval_metric_fn_key] = {
          'recall_lower_bound': (eval_config.recall_lower_bound),
          'recall_upper_bound': (eval_config.recall_upper_bound),
          'skip_predictions_for_unlabeled_class':
              eval_config.skip_predictions_for_unlabeled_class,
      }
  return evaluator_options
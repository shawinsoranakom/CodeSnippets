def _reduce_instance_metrics(
      self, logs: Dict[str, Any], use_masks: bool = False
  ):
    """Updates the per class and mean instance metrics in the logs."""
    if use_masks:
      instance_metrics = self.instance_mask_perclass_metrics
      prefix = 'mask_'
    else:
      instance_metrics = self.instance_box_perclass_metrics
      prefix = ''
    if instance_metrics is None:
      raise ValueError(
          'No instance metrics defined when use_masks is %s' % use_masks
      )
    result = instance_metrics.result()
    iou_thresholds = instance_metrics.get_config()['iou_thresholds']

    for ap_key in instance_metrics.get_average_precision_metrics_keys():
      # (num_iou_thresholds, num_classes)
      per_class_ap = tf.where(
          result['valid_classes'], result[ap_key], tf.zeros_like(result[ap_key])
      )
      # (num_iou_thresholds,)
      mean_ap_by_iou = tf.math.divide_no_nan(
          tf.reduce_sum(per_class_ap, axis=-1),
          tf.reduce_sum(
              tf.cast(result['valid_classes'], dtype=per_class_ap.dtype),
              axis=-1,
          ),
      )
      logs[f'{prefix}{ap_key}'] = tf.reduce_mean(mean_ap_by_iou)
      for j, iou in enumerate(iou_thresholds):
        if int(iou * 100) in {50, 75}:
          logs[f'{prefix}{ap_key}{int(iou * 100)}'] = mean_ap_by_iou[j]

      if self.task_config.per_category_metrics:
        # (num_classes,)
        per_class_mean_ap = tf.reduce_mean(per_class_ap, axis=0)
        valid_classes = result['valid_classes'].numpy()
        for k in range(self.task_config.model.num_classes):
          if valid_classes[k]:
            logs[f'{prefix}{ap_key} ByCategory/{k}'] = per_class_mean_ap[k]
            for j, iou in enumerate(iou_thresholds):
              if int(iou * 100) in {50, 75}:
                logs[f'{prefix}{ap_key}{int(iou * 100)} ByCategory/{k}'] = (
                    per_class_ap[j][k]
                )
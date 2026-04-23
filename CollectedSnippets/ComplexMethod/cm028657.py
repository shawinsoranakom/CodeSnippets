def reduce_aggregated_logs(self, aggregated_logs, global_step=None):
    result = {}
    ious = self.perclass_iou_metric.result()
    if self.task_config.evaluation.report_per_class_iou:
      for i, value in enumerate(ious.numpy()):
        result.update({'segmentation_iou/class_{}'.format(i): value})

    # Computes mean IoU
    result.update({'segmentation_mean_iou': tf.reduce_mean(ious).numpy()})

    if self.task_config.model.generate_panoptic_masks:
      panoptic_quality_results = self.panoptic_quality_metric.result()
      for k, value in panoptic_quality_results.items():
        if k.endswith('per_class'):
          if self.task_config.evaluation.report_per_class_pq:
            for i, per_class_value in enumerate(value):
              metric_key = 'panoptic_quality/{}/class_{}'.format(k, i)
              result[metric_key] = per_class_value
          else:
            continue
        else:
          result['panoptic_quality/{}'.format(k)] = value

    return result
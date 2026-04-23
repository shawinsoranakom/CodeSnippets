def evaluate(self):
    """Compute evaluation result.

    Returns:
      A dictionary of metrics with the following fields -

      1. summary_metrics:
        '<prefix if not empty>_Precision/mAP@<matching_iou_threshold>IOU': mean
        average precision at the specified IOU threshold.

      2. per_category_ap: category specific results with keys of the form
        '<prefix if not empty>_PerformanceByCategory/
        mAP@<matching_iou_threshold>IOU/category'.
    """
    (per_class_ap, mean_ap, per_class_precision, per_class_recall,
     per_class_corloc, mean_corloc) = (
         self._evaluation.evaluate())
    pascal_metrics = {self._metric_names[0]: mean_ap}
    if self._evaluate_corlocs:
      pascal_metrics[self._metric_names[1]] = mean_corloc
    category_index = label_map_util.create_category_index(self._categories)
    for idx in range(per_class_ap.size):
      if idx + self._label_id_offset in category_index:
        category_name = category_index[idx + self._label_id_offset]['name']
        try:
          category_name = six.text_type(category_name, 'utf-8')
        except TypeError:
          pass
        category_name = unicodedata.normalize('NFKD', category_name)
        if six.PY2:
          category_name = category_name.encode('ascii', 'ignore')
        display_name = (
            self._metric_prefix + 'PerformanceByCategory/AP@{}IOU/{}'.format(
                self._matching_iou_threshold, category_name))
        pascal_metrics[display_name] = per_class_ap[idx]

        # Optionally add precision and recall values
        if self._evaluate_precision_recall:
          display_name = (
              self._metric_prefix +
              'PerformanceByCategory/Precision@{}IOU/{}'.format(
                  self._matching_iou_threshold, category_name))
          pascal_metrics[display_name] = per_class_precision[idx]
          display_name = (
              self._metric_prefix +
              'PerformanceByCategory/Recall@{}IOU/{}'.format(
                  self._matching_iou_threshold, category_name))
          pascal_metrics[display_name] = per_class_recall[idx]

        # Optionally add CorLoc metrics.classes
        if self._evaluate_corlocs:
          display_name = (
              self._metric_prefix +
              'PerformanceByCategory/CorLoc@{}IOU/{}'.format(
                  self._matching_iou_threshold, category_name))
          pascal_metrics[display_name] = per_class_corloc[idx]

    return pascal_metrics
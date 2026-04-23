def _build_metric_names(self):
    """Builds a list with metric names."""
    if self._recall_lower_bound > 0.0 or self._recall_upper_bound < 1.0:
      self._metric_names = [
          self._metric_prefix +
          'Precision/mAP@{}IOU@[{:.1f},{:.1f}]Recall'.format(
              self._matching_iou_threshold, self._recall_lower_bound,
              self._recall_upper_bound)
      ]
    else:
      self._metric_names = [
          self._metric_prefix +
          'Precision/mAP@{}IOU'.format(self._matching_iou_threshold)
      ]
    if self._evaluate_corlocs:
      self._metric_names.append(
          self._metric_prefix +
          'Precision/meanCorLoc@{}IOU'.format(self._matching_iou_threshold))

    category_index = label_map_util.create_category_index(self._categories)
    for idx in range(self._num_classes):
      if idx + self._label_id_offset in category_index:
        category_name = category_index[idx + self._label_id_offset]['name']
        try:
          category_name = six.text_type(category_name, 'utf-8')
        except TypeError:
          pass
        category_name = unicodedata.normalize('NFKD', category_name)
        if six.PY2:
          category_name = category_name.encode('ascii', 'ignore')
        self._metric_names.append(
            self._metric_prefix + 'PerformanceByCategory/AP@{}IOU/{}'.format(
                self._matching_iou_threshold, category_name))
        if self._evaluate_corlocs:
          self._metric_names.append(
              self._metric_prefix +
              'PerformanceByCategory/CorLoc@{}IOU/{}'.format(
                  self._matching_iou_threshold, category_name))
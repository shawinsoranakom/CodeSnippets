def ComputeMetrics(self,
                     include_metrics_per_category=False,
                     all_metrics_per_category=False,
                     super_categories=None):
    """Computes detection/keypoint metrics.

    Args:
      include_metrics_per_category: If True, will include metrics per category.
      all_metrics_per_category: If true, include all the summery metrics for
        each category in per_category_ap. Be careful with setting it to true if
        you have more than handful of categories, because it will pollute
        your mldash.
      super_categories: None or a python dict mapping super-category names
        (strings) to lists of categories (corresponding to category names
        in the label_map).  Metrics are aggregated along these super-categories
        and added to the `per_category_ap` and are associated with the name
          `PerformanceBySuperCategory/<super-category-name>`.

    Returns:
      1. summary_metrics: a dictionary holding:
        'Precision/mAP': mean average precision over classes averaged over IOU
          thresholds ranging from .5 to .95 with .05 increments
        'Precision/mAP@.50IOU': mean average precision at 50% IOU
        'Precision/mAP@.75IOU': mean average precision at 75% IOU
        'Precision/mAP (small)': mean average precision for small objects
                        (area < 32^2 pixels). NOTE: not present for 'keypoints'
        'Precision/mAP (medium)': mean average precision for medium sized
                        objects (32^2 pixels < area < 96^2 pixels)
        'Precision/mAP (large)': mean average precision for large objects
                        (96^2 pixels < area < 10000^2 pixels)
        'Recall/AR@1': average recall with 1 detection
        'Recall/AR@10': average recall with 10 detections
        'Recall/AR@100': average recall with 100 detections
        'Recall/AR@100 (small)': average recall for small objects with 100
          detections. NOTE: not present for 'keypoints'
        'Recall/AR@100 (medium)': average recall for medium objects with 100
          detections
        'Recall/AR@100 (large)': average recall for large objects with 100
          detections
      2. per_category_ap: a dictionary holding category specific results with
        keys of the form: 'Precision mAP ByCategory/category'
        (without the supercategory part if no supercategories exist).
        For backward compatibility 'PerformanceByCategory' is included in the
        output regardless of all_metrics_per_category.
        If evaluating class-agnostic mode, per_category_ap is an empty
        dictionary.
        If super_categories are provided, then this will additionally include
        metrics aggregated along the super_categories with keys of the form:
        `PerformanceBySuperCategory/<super-category-name>`

    Raises:
      ValueError: If category_stats does not exist.
    """
    self.evaluate()
    self.accumulate()
    self.summarize()

    summary_metrics = {}
    if self._iou_type in ['bbox', 'segm']:
      summary_metrics = OrderedDict(
          [(name, self.stats[index]) for name, index in
           COCO_METRIC_NAMES_AND_INDEX])
    elif self._iou_type == 'keypoints':
      category_id = self.GetCategoryIdList()[0]
      category_name = self.GetCategory(category_id)['name']
      summary_metrics = OrderedDict([])
      for metric_name, index in COCO_KEYPOINT_METRIC_NAMES_AND_INDEX:
        value = self.stats[index]
        summary_metrics['{} ByCategory/{}'.format(
            metric_name, category_name)] = value
    if not include_metrics_per_category:
      return summary_metrics, {}
    if not hasattr(self, 'category_stats'):
      raise ValueError('Category stats do not exist')
    per_category_ap = OrderedDict([])
    super_category_ap = OrderedDict([])
    if self.GetAgnosticMode():
      return summary_metrics, per_category_ap

    if super_categories:
      for key in super_categories:
        super_category_ap['PerformanceBySuperCategory/{}'.format(key)] = 0

        if all_metrics_per_category:
          for metric_name, _ in COCO_METRIC_NAMES_AND_INDEX:
            metric_key = '{} BySuperCategory/{}'.format(metric_name, key)
            super_category_ap[metric_key] = 0

    for category_index, category_id in enumerate(self.GetCategoryIdList()):
      category = self.GetCategory(category_id)['name']
      # Kept for backward compatilbility
      per_category_ap['PerformanceByCategory/mAP/{}'.format(
          category)] = self.category_stats[0][category_index]

      if all_metrics_per_category:
        for metric_name, index in COCO_METRIC_NAMES_AND_INDEX:
          metric_key = '{} ByCategory/{}'.format(metric_name, category)
          per_category_ap[metric_key] = self.category_stats[index][
              category_index]

      if super_categories:
        for key in super_categories:
          if category in super_categories[key]:
            metric_key = 'PerformanceBySuperCategory/{}'.format(key)
            super_category_ap[metric_key] += self.category_stats[0][
                category_index]
            if all_metrics_per_category:
              for metric_name, index in COCO_METRIC_NAMES_AND_INDEX:
                metric_key = '{} BySuperCategory/{}'.format(metric_name, key)
                super_category_ap[metric_key] += (
                    self.category_stats[index][category_index])

    if super_categories:
      for key in super_categories:
        length = len(super_categories[key])
        super_category_ap['PerformanceBySuperCategory/{}'.format(
            key)] /= length

        if all_metrics_per_category:
          for metric_name, _ in COCO_METRIC_NAMES_AND_INDEX:
            super_category_ap['{} BySuperCategory/{}'.format(
                metric_name, key)] /= length

      per_category_ap.update(super_category_ap)
    return summary_metrics, per_category_ap
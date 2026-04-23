def evaluate(self):
    """Evaluates with detections from all images with COCO API.

    Returns:
      coco_metric: float numpy array with shape [24] representing the
        coco-style evaluation metrics (box and mask).
    """
    if not self._annotation_file:
      gt_dataset = coco_utils.convert_groundtruths_to_coco_dataset(
          self._groundtruths)
      coco_gt = coco_utils.COCOWrapper(
          eval_type=('mask' if self._include_mask else 'box'),
          gt_dataset=gt_dataset)
    else:
      coco_gt = self._coco_gt
    coco_predictions = coco_utils.convert_predictions_to_coco_annotations(
        self._predictions)
    coco_dt = coco_gt.loadRes(predictions=coco_predictions)
    image_ids = [ann['image_id'] for ann in coco_predictions]

    coco_eval = cocoeval.COCOeval(coco_gt, coco_dt, iouType='bbox')
    coco_eval.params.imgIds = image_ids
    coco_eval.evaluate()
    coco_eval.accumulate()
    coco_eval.summarize()
    coco_metrics = coco_eval.stats

    if self._include_mask:
      mcoco_eval = cocoeval.COCOeval(coco_gt, coco_dt, iouType='segm')
      mcoco_eval.params.imgIds = image_ids
      mcoco_eval.evaluate()
      mcoco_eval.accumulate()
      mcoco_eval.summarize()
      if self._mask_eval_class == 'all':
        metrics = np.hstack((coco_metrics, mcoco_eval.stats))
      else:
        mask_coco_metrics = mcoco_eval.category_stats
        val_catg_idx = np.isin(mcoco_eval.params.catIds, self._eval_categories)
        # Gather the valid evaluation of the eval categories.
        if np.any(val_catg_idx):
          mean_val_metrics = []
          for mid in range(len(self._metric_names) // 2):
            mean_val_metrics.append(
                np.nanmean(mask_coco_metrics[mid][val_catg_idx]))

          mean_val_metrics = np.array(mean_val_metrics)
        else:
          mean_val_metrics = np.zeros(len(self._metric_names) // 2)
        metrics = np.hstack((coco_metrics, mean_val_metrics))
    else:
      metrics = coco_metrics

    # Cleans up the internal variables in order for a fresh eval next time.
    self.reset()

    metrics_dict = {}
    for i, name in enumerate(self._metric_names):
      metrics_dict[name] = metrics[i].astype(np.float32)
    return metrics_dict
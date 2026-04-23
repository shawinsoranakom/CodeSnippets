def evaluate(self):
    """Evaluates with detections from all images with COCO API.

    Returns:
      coco_metric: float numpy array with shape [24] representing the
        coco-style evaluation metrics (box and mask).
    """
    if not self._annotation_file:
      logging.info('Thre is no annotation_file in COCOEvaluator.')
      gt_dataset = coco_utils.convert_groundtruths_to_coco_dataset(
          self._groundtruths)
      coco_gt = coco_utils.COCOWrapper(
          eval_type=('mask' if self._include_mask else 'box'),
          gt_dataset=gt_dataset)
    else:
      logging.info('Using annotation file: %s', self._annotation_file)
      coco_gt = self._coco_gt

    coco_predictions = coco_utils.convert_predictions_to_coco_annotations(
        self._predictions)
    coco_dt = coco_gt.loadRes(predictions=coco_predictions)
    image_ids = [ann['image_id'] for ann in coco_predictions]
    # Class manipulation: 'all' split samples -> ignored_split = 0.
    for idx, ann in enumerate(coco_gt.dataset['annotations']):
      coco_gt.dataset['annotations'][idx]['ignored_split'] = 0
    coco_eval = cocoeval.OlnCOCOevalXclassWrapper(
        coco_gt, coco_dt, iou_type='bbox')
    coco_eval.params.maxDets = [10, 20, 50, 100, 200]
    coco_eval.params.imgIds = image_ids
    coco_eval.params.useCats = 0 if not self._use_category else 1
    coco_eval.evaluate()
    coco_eval.accumulate()
    coco_eval.summarize()
    coco_metrics = coco_eval.stats

    if self._include_mask:
      mcoco_eval = cocoeval.OlnCOCOevalXclassWrapper(
          coco_gt, coco_dt, iou_type='segm')
      mcoco_eval.params.maxDets = [10, 20, 50, 100, 200]
      mcoco_eval.params.imgIds = image_ids
      mcoco_eval.params.useCats = 0 if not self._use_category else 1
      mcoco_eval.evaluate()
      mcoco_eval.accumulate()
      mcoco_eval.summarize()
      mask_coco_metrics = mcoco_eval.stats

    if self._include_mask:
      metrics = np.hstack((coco_metrics, mask_coco_metrics))
    else:
      metrics = coco_metrics

    if self._seen_class != 'all':
      # for seen class eval, samples of novel_class are ignored.
      coco_gt_seen = copy.deepcopy(coco_gt)
      for idx, ann in enumerate(coco_gt.dataset['annotations']):
        if ann['category_id'] in self._seen_class_ids:
          coco_gt_seen.dataset['annotations'][idx]['ignored_split'] = 0
        else:
          coco_gt_seen.dataset['annotations'][idx]['ignored_split'] = 1
      coco_eval_seen = cocoeval.OlnCOCOevalXclassWrapper(
          coco_gt_seen, coco_dt, iou_type='bbox')
      coco_eval_seen.params.maxDets = [10, 20, 50, 100, 200]
      coco_eval_seen.params.imgIds = image_ids
      coco_eval_seen.params.useCats = 0 if not self._use_category else 1
      coco_eval_seen.evaluate()
      coco_eval_seen.accumulate()
      coco_eval_seen.summarize()
      coco_metrics_seen = coco_eval_seen.stats
      if self._include_mask:
        mcoco_eval_seen = cocoeval.OlnCOCOevalXclassWrapper(
            coco_gt_seen, coco_dt, iou_type='segm')
        mcoco_eval_seen.params.maxDets = [10, 20, 50, 100, 200]
        mcoco_eval_seen.params.imgIds = image_ids
        mcoco_eval_seen.params.useCats = 0 if not self._use_category else 1
        mcoco_eval_seen.evaluate()
        mcoco_eval_seen.accumulate()
        mcoco_eval_seen.summarize()
        mask_coco_metrics_seen = mcoco_eval_seen.stats

      # for novel class eval, samples of seen_class are ignored.
      coco_gt_novel = copy.deepcopy(coco_gt)
      for idx, ann in enumerate(coco_gt.dataset['annotations']):
        if ann['category_id'] in self._seen_class_ids:
          coco_gt_novel.dataset['annotations'][idx]['ignored_split'] = 1
        else:
          coco_gt_novel.dataset['annotations'][idx]['ignored_split'] = 0
      coco_eval_novel = cocoeval.OlnCOCOevalXclassWrapper(
          coco_gt_novel, coco_dt, iou_type='bbox')
      coco_eval_novel.params.maxDets = [10, 20, 50, 100, 200]
      coco_eval_novel.params.imgIds = image_ids
      coco_eval_novel.params.useCats = 0 if not self._use_category else 1
      coco_eval_novel.evaluate()
      coco_eval_novel.accumulate()
      coco_eval_novel.summarize()
      coco_metrics_novel = coco_eval_novel.stats
      if self._include_mask:
        mcoco_eval_novel = cocoeval.OlnCOCOevalXclassWrapper(
            coco_gt_novel, coco_dt, iou_type='segm')
        mcoco_eval_novel.params.maxDets = [10, 20, 50, 100, 200]
        mcoco_eval_novel.params.imgIds = image_ids
        mcoco_eval_novel.params.useCats = 0 if not self._use_category else 1
        mcoco_eval_novel.evaluate()
        mcoco_eval_novel.accumulate()
        mcoco_eval_novel.summarize()
        mask_coco_metrics_novel = mcoco_eval_novel.stats

      # Combine all splits.
      if self._include_mask:
        metrics = np.hstack((
            coco_metrics, coco_metrics_seen, coco_metrics_novel,
            mask_coco_metrics, mask_coco_metrics_seen, mask_coco_metrics_novel))
      else:
        metrics = np.hstack((
            coco_metrics, coco_metrics_seen, coco_metrics_novel))

    # Cleans up the internal variables in order for a fresh eval next time.
    self.reset()

    metrics_dict = {}
    for i, name in enumerate(self._metric_names):
      metrics_dict[name] = metrics[i].astype(np.float32)
    return metrics_dict
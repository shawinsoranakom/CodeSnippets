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
    for idx, _ in enumerate(coco_gt.dataset['annotations']):
      coco_gt.dataset['annotations'][idx]['ignored_split'] = 0
    coco_eval = cocoeval.OlnCOCOevalWrapper(coco_gt, coco_dt, iou_type='bbox')
    coco_eval.params.maxDets = [10, 20, 50, 100, 200]
    coco_eval.params.imgIds = image_ids
    coco_eval.params.useCats = 0 if not self._use_category else 1
    coco_eval.evaluate()
    coco_eval.accumulate()
    coco_eval.summarize()
    coco_metrics = coco_eval.stats

    if self._include_mask:
      mcoco_eval = cocoeval.OlnCOCOevalWrapper(coco_gt, coco_dt,
                                               iou_type='segm')
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

    # Cleans up the internal variables in order for a fresh eval next time.
    self.reset()

    metrics_dict = {}
    for i, name in enumerate(self._metric_names):
      metrics_dict[name] = metrics[i].astype(np.float32)
    return metrics_dict
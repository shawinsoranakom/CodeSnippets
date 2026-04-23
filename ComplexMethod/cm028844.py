def evaluate(self):
    """Evaluates with detections from all images with COCO API.

    Returns:
      coco_metric: float numpy array with shape [24] representing the
        coco-style evaluation metrics (box and mask).
    """
    if not self._annotation_file:
      logging.info('There is no annotation_file in COCOEvaluator.')
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

    coco_eval = cocoeval.COCOeval(coco_gt, coco_dt, iouType='bbox')
    coco_eval.params.imgIds = image_ids
    coco_eval.params.maxDets[2] = self.max_num_eval_detections
    coco_eval.evaluate()
    coco_eval.accumulate()
    coco_eval.summarize()
    coco_metrics = coco_eval.stats
    metrics = coco_metrics

    if self._include_mask:
      mcoco_eval = cocoeval.COCOeval(coco_gt, coco_dt, iouType='segm')
      mcoco_eval.params.imgIds = image_ids
      mcoco_eval.evaluate()
      mcoco_eval.accumulate()
      mcoco_eval.summarize()
      mask_coco_metrics = mcoco_eval.stats
      metrics = np.hstack((metrics, mask_coco_metrics))

    if self._include_keypoint:
      kcoco_eval = cocoeval.COCOeval(coco_gt, coco_dt, iouType='keypoints',
                                     kpt_oks_sigmas=self._kpt_oks_sigmas)
      kcoco_eval.params.imgIds = image_ids
      kcoco_eval.evaluate()
      kcoco_eval.accumulate()
      kcoco_eval.summarize()
      keypoint_coco_metrics = kcoco_eval.stats
      metrics = np.hstack((metrics, keypoint_coco_metrics))

    metrics_dict = {}
    for i, name in enumerate(self._metric_names):
      metrics_dict[name] = metrics[i].astype(np.float32)

    # Adds metrics per category.
    if self._per_category_metrics:
      metrics_dict.update(self._retrieve_per_category_metrics(coco_eval))

      if self._include_mask:
        metrics_dict.update(self._retrieve_per_category_metrics(
            mcoco_eval, prefix='mask'))

      if self._include_keypoint:
        metrics_dict.update(self._retrieve_per_category_metrics(
            mcoco_eval, prefix='keypoints'))

    return metrics_dict
def build_metrics(self, training: bool = True):
    """Build detection metrics."""
    metrics = []
    metric_names = ['total_loss', 'cls_loss', 'box_loss', 'model_loss']
    for name in metric_names:
      metrics.append(tf_keras.metrics.Mean(name, dtype=tf.float32))

    if not training:
      if (
          self.task_config.validation_data.tfds_name
          and self.task_config.annotation_file
      ):
        raise ValueError(
            "Can't evaluate using annotation file when TFDS is used."
        )
      if self._task_config.use_coco_metrics:
        self.coco_metric = coco_evaluator.COCOEvaluator(
            annotation_file=self.task_config.annotation_file,
            include_mask=False,
            per_category_metrics=self.task_config.per_category_metrics,
            max_num_eval_detections=self.task_config.max_num_eval_detections,
        )
      if self._task_config.use_wod_metrics:
        # To use Waymo open dataset metrics, please install one of the pip
        # package `waymo-open-dataset-tf-*` from
        # https://github.com/waymo-research/waymo-open-dataset/blob/master/docs/quick_start.md#use-pre-compiled-pippip3-packages-for-linux
        # Note that the package is built with specific tensorflow version and
        # will produce error if it does not match the tf version that is
        # currently used.
        try:
          from official.vision.evaluation import wod_detection_evaluator  # pylint: disable=g-import-not-at-top
        except ModuleNotFoundError:
          logging.error('waymo-open-dataset should be installed to enable Waymo'
                        ' evaluator.')
          raise
        self.wod_metric = wod_detection_evaluator.WOD2dDetectionEvaluator()

    return metrics
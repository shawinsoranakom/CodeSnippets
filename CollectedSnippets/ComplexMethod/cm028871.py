def build_metrics(self, training: bool = True):
    """Builds detection metrics."""
    self.instance_box_perclass_metrics = None
    self.instance_mask_perclass_metrics = None
    if training:
      metric_names = [
          'total_loss',
          'rpn_score_loss',
          'rpn_box_loss',
          'frcnn_cls_loss',
          'frcnn_box_loss',
          'mask_loss',
          'model_loss',
      ]
      return [
          tf_keras.metrics.Mean(name, dtype=tf.float32) for name in metric_names
      ]
    else:
      if self._task_config.use_coco_metrics:
        self._build_coco_metrics()
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

      if self.task_config.use_approx_instance_metrics:
        self.instance_box_perclass_metrics = metrics_lib.InstanceMetrics(
            name='instance_box_perclass',
            num_classes=self.task_config.model.num_classes,
            iou_thresholds=np.arange(0.5, 1.0, step=0.05),
        )
        if self.task_config.model.include_mask:
          self.instance_mask_perclass_metrics = metrics_lib.InstanceMetrics(
              name='instance_mask_perclass',
              use_masks=True,
              num_classes=self.task_config.model.num_classes,
              iou_thresholds=np.arange(0.5, 1.0, step=0.05),
          )

      return []
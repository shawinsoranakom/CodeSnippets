def build_metrics(self,
                    training: bool = True) -> List[tf_keras.metrics.Metric]:
    """Gets streaming metrics for training/validation."""
    is_multilabel = self.task_config.train_data.is_multilabel
    if not is_multilabel:
      k = self.task_config.evaluation.top_k
      if (self.task_config.losses.one_hot or
          self.task_config.losses.soft_labels):
        metrics = [
            tf_keras.metrics.CategoricalAccuracy(name='accuracy'),
            tf_keras.metrics.TopKCategoricalAccuracy(
                k=k, name='top_{}_accuracy'.format(k))]
        if hasattr(
            self.task_config.evaluation, 'precision_and_recall_thresholds'
        ) and self.task_config.evaluation.precision_and_recall_thresholds:
          thresholds = self.task_config.evaluation.precision_and_recall_thresholds  # pylint: disable=line-too-long
          # pylint:disable=g-complex-comprehension
          metrics += [
              tf_keras.metrics.Precision(
                  thresholds=th,
                  name='precision_at_threshold_{}'.format(th),
                  top_k=1) for th in thresholds
          ]
          metrics += [
              tf_keras.metrics.Recall(
                  thresholds=th,
                  name='recall_at_threshold_{}'.format(th),
                  top_k=1) for th in thresholds
          ]

          # Add per-class precision and recall.
          if hasattr(
              self.task_config.evaluation,
              'report_per_class_precision_and_recall'
          ) and self.task_config.evaluation.report_per_class_precision_and_recall:
            for class_id in range(self.task_config.model.num_classes):
              metrics += [
                  tf_keras.metrics.Precision(
                      thresholds=th,
                      class_id=class_id,
                      name=f'precision_at_threshold_{th}/{class_id}',
                      top_k=1) for th in thresholds
              ]
              metrics += [
                  tf_keras.metrics.Recall(
                      thresholds=th,
                      class_id=class_id,
                      name=f'recall_at_threshold_{th}/{class_id}',
                      top_k=1) for th in thresholds
              ]
              # pylint:enable=g-complex-comprehension
      else:
        metrics = [
            tf_keras.metrics.SparseCategoricalAccuracy(name='accuracy'),
            tf_keras.metrics.SparseTopKCategoricalAccuracy(
                k=k, name='top_{}_accuracy'.format(k))]
    else:
      metrics = []
      # These metrics destablize the training if included in training. The jobs
      # fail due to OOM.
      # TODO(arashwan): Investigate adding following metric to train.
      if not training:
        metrics = [
            tf_keras.metrics.AUC(
                name='globalPR-AUC',
                curve='PR',
                multi_label=False,
                from_logits=True),
            tf_keras.metrics.AUC(
                name='meanPR-AUC',
                curve='PR',
                multi_label=True,
                num_labels=self.task_config.model.num_classes,
                from_logits=True),
        ]
    return metrics
def validation_step(self,
                      inputs: Tuple[Any, Any],
                      model: tf_keras.Model,
                      metrics: Optional[List[Any]] = None):
    """Validation step.

    Args:
      inputs: a dictionary of input tensors.
      model: the keras.Model.
      metrics: a nested structure of metrics objects.

    Returns:
      A dictionary of logs.
    """
    features, labels = inputs

    input_partition_dims = self.task_config.eval_input_partition_dims
    if input_partition_dims:
      strategy = tf.distribute.get_strategy()
      features = strategy.experimental_split_to_logical_devices(
          features, input_partition_dims)

    outputs = self.inference_step(features, model)
    if isinstance(outputs, tf.Tensor):
      outputs = {'logits': outputs}
    outputs = tf.nest.map_structure(lambda x: tf.cast(x, tf.float32), outputs)

    if self.task_config.validation_data.resize_eval_groundtruth:
      loss = self.build_losses(
          model_outputs=outputs, labels=labels, aux_losses=model.losses)
    else:
      loss = 0

    logs = {self.loss: loss}

    if self.iou_metric is not None:
      self.iou_metric.update_state(labels, outputs['logits'])
    if metrics:
      self.process_metrics(metrics, labels, outputs)

    if (
        hasattr(self.task_config, 'allow_image_summary')
        and self.task_config.allow_image_summary
    ):
      logs.update(
          {'visualization': (tf.cast(features, dtype=tf.float32), outputs)}
      )

    return logs
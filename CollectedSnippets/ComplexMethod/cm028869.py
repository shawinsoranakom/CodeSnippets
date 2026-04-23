def validation_step(self,
                      inputs: Tuple[Any, Any],
                      model: tf_keras.Model,
                      metrics: Optional[List[Any]] = None):
    """Runs validation step.

    Args:
      inputs: A tuple of input tensors of (features, labels).
      model: A tf_keras.Model instance.
      metrics: A nested structure of metrics objects.

    Returns:
      A dictionary of logs.
    """
    features, labels = inputs
    one_hot = self.task_config.losses.one_hot
    soft_labels = self.task_config.losses.soft_labels
    is_multilabel = self.task_config.train_data.is_multilabel
    # Note: `soft_labels`` only apply to the training phrase. In the validation
    # phrase, labels should still be integer ids and need to be converted to
    # one hot format.
    if (one_hot or soft_labels) and not is_multilabel:
      labels = tf.one_hot(labels, self.task_config.model.num_classes)

    outputs = self.inference_step(features, model)
    outputs = tf.nest.map_structure(lambda x: tf.cast(x, tf.float32), outputs)
    loss = self.build_losses(
        model_outputs=outputs,
        labels=labels,
        aux_losses=model.losses)

    logs = {self.loss: loss}
    # Convert logits to softmax for metric computation if needed.
    if hasattr(self.task_config.model,
               'output_softmax') and self.task_config.model.output_softmax:
      outputs = tf.nn.softmax(outputs, axis=-1)
    if metrics:
      self.process_metrics(metrics, labels, outputs)
    elif model.compiled_metrics:
      self.process_compiled_metrics(model.compiled_metrics, labels, outputs)
      logs.update({m.name: m.result() for m in model.metrics})
    return logs
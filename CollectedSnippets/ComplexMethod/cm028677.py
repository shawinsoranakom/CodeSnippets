def validation_step(self, inputs, model: tf_keras.Model, metrics=None):
    """Validation step.

    With distribution strategies, this method runs on devices.

    Args:
      inputs: a dictionary of input tensors.
      model: the keras.Model.
      metrics: a nested structure of metrics objects.

    Returns:
      A dictionary of logs.
    """
    if isinstance(inputs, tuple) and len(inputs) == 2:
      features, labels = inputs
    else:
      features, labels = inputs, inputs
    outputs = self.inference_step(features, model)
    loss = self.build_losses(
        labels=labels, model_outputs=outputs, aux_losses=model.losses)
    logs = {self.loss: loss}
    if metrics:
      self.process_metrics(metrics, labels, outputs)
    if model.compiled_metrics:
      self.process_compiled_metrics(model.compiled_metrics, labels, outputs)
      logs.update({m.name: m.result() for m in metrics or []})
      logs.update({m.name: m.result() for m in model.metrics})
    return logs
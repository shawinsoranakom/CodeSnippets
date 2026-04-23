def train_step(self,
                 inputs,
                 model: tf_keras.Model,
                 optimizer: tf_keras.optimizers.Optimizer,
                 metrics=None):
    """Does forward and backward.

    With distribution strategies, this method runs on devices.

    Args:
      inputs: a dictionary of input tensors.
      model: the model, forward pass definition.
      optimizer: the optimizer for this training step.
      metrics: a nested structure of metrics objects.

    Returns:
      A dictionary of logs.
    """
    if isinstance(inputs, tuple) and len(inputs) == 2:
      features, labels = inputs
    else:
      features, labels = inputs, inputs
    with tf.GradientTape() as tape:
      outputs = model(features, training=True)
      # Computes per-replica loss.
      if model.compiled_loss:
        loss = model.compiled_loss(
            labels, outputs, regularization_losses=model.losses)
        loss += self.build_losses(
            labels=labels, model_outputs=outputs, aux_losses=None)
      else:
        loss = self.build_losses(
            labels=labels, model_outputs=outputs, aux_losses=model.losses)
      # Scales loss as the default gradients allreduce performs sum inside the
      # optimizer.
      scaled_loss = loss / tf.distribute.get_strategy().num_replicas_in_sync

      # For mixed precision, when a LossScaleOptimizer is used, the loss is
      # scaled to avoid numeric underflow.
      if isinstance(optimizer,
                    tf_keras.mixed_precision.LossScaleOptimizer):
        scaled_loss = optimizer.get_scaled_loss(scaled_loss)

    tvars = model.trainable_variables
    grads = tape.gradient(scaled_loss, tvars)

    if isinstance(optimizer,
                  tf_keras.mixed_precision.LossScaleOptimizer):
      grads = optimizer.get_unscaled_gradients(grads)
    optimizer.apply_gradients(list(zip(grads, tvars)))
    logs = {self.loss: loss}
    if metrics:
      self.process_metrics(metrics, labels, outputs)
    if model.compiled_metrics:
      self.process_compiled_metrics(model.compiled_metrics, labels, outputs)
      logs.update({m.name: m.result() for m in metrics or []})
      logs.update({m.name: m.result() for m in model.metrics})
    return logs
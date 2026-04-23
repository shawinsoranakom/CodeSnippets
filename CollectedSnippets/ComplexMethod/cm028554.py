def train_step(self,
                 inputs: Mapping[str, Any],
                 model: tf_keras.Model,
                 optimizer: tf_keras.optimizers.Optimizer,
                 metrics: Optional[List[Any]] = None):
    """Does forward and backward pass.

    Args:
      inputs: a dictionary of input tensors.
      model: the model, forward pass definition.
      optimizer: the optimizer for this training step.
      metrics: a nested structure of metrics objects.

    Returns:
      A dictionary of logs.
    """
    features = inputs['image']
    labels = [inputs[k] for k in self._get_label_names()]

    num_replicas = tf.distribute.get_strategy().num_replicas_in_sync
    with tf.GradientTape() as tape:
      outputs = model(features, training=True)
      # tf_keras.Model eliminates the list if the outputs list len is 1.
      # Recover it here to be compatible with multihead settings.
      outputs = [outputs] if isinstance(outputs, tf.Tensor) else outputs
      # Casting output layer as float32 is necessary when mixed_precision is
      # mixed_float16 or mixed_bfloat16 to ensure output is casted as float32.
      outputs = tf.nest.map_structure(lambda x: tf.cast(x, tf.float32), outputs)

      if self._is_multilabel():
        outputs = tf.nest.map_structure(tf.math.sigmoid, outputs)
      else:
        outputs = tf.nest.map_structure(tf.math.softmax, outputs)

      all_losses = self.build_losses(model_outputs=outputs,
                                     labels=labels,
                                     aux_losses=model.losses)

      # Scale loss as the default gradients allreduce performs sum inside the
      # optimizer.
      scaled_loss = all_losses / num_replicas

      # For mixed_precision policy, when LossScaleOptimizer is used, loss is
      # scaled for numerical stability.
      if isinstance(
          optimizer, tf_keras.mixed_precision.LossScaleOptimizer):
        scaled_loss = optimizer.get_scaled_loss(scaled_loss)

    tvars = model.trainable_variables
    grads = tape.gradient(scaled_loss, tvars)
    # Scale back gradient before apply_gradients when LossScaleOptimizer is
    # used.
    if isinstance(optimizer, tf_keras.mixed_precision.LossScaleOptimizer):
      grads = optimizer.get_unscaled_gradients(grads)
    optimizer.apply_gradients(list(zip(grads, tvars)))

    logs = {self.loss: all_losses}
    if metrics:
      self.process_metrics(metrics, labels, outputs)
      logs.update({m.name: m.result() for m in metrics})
    return logs
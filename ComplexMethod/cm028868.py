def train_step(self,
                 inputs: Tuple[Any, Any],
                 model: tf_keras.Model,
                 optimizer: tf_keras.optimizers.Optimizer,
                 metrics: Optional[List[Any]] = None):
    """Does forward and backward.

    Args:
      inputs: A tuple of input tensors of (features, labels).
      model: A tf_keras.Model instance.
      optimizer: The optimizer for this training step.
      metrics: A nested structure of metrics objects.

    Returns:
      A dictionary of logs.
    """
    features, labels = inputs

    is_multilabel = self.task_config.train_data.is_multilabel
    if self.task_config.losses.one_hot and not is_multilabel:
      labels = tf.one_hot(labels, self.task_config.model.num_classes)

    if self.task_config.losses.use_binary_cross_entropy:
      # BCE loss converts the multiclass classification to multilabel. The
      # corresponding label value of objects present in the image would be one.
      if self.task_config.train_data.mixup_and_cutmix is not None:
        # label values below off_value_threshold would be mapped to zero and
        # above that would be mapped to one. Negative labels are guaranteed to
        # have value less than or equal value of the off_value from mixup.
        off_value_threshold = (
            self.task_config.train_data.mixup_and_cutmix.label_smoothing
            / self.task_config.model.num_classes
        )
        labels = tf.where(
            tf.less(labels, off_value_threshold + _EPSILON), 0.0, 1.0)
      elif tf.rank(labels) == 1:
        labels = tf.one_hot(labels, self.task_config.model.num_classes)

    num_replicas = tf.distribute.get_strategy().num_replicas_in_sync
    with tf.GradientTape() as tape:
      outputs = model(features, training=True)

      # Casting output layer as float32 is necessary when mixed_precision is
      # mixed_float16 or mixed_bfloat16 to ensure output is casted as float32.
      outputs = tf.nest.map_structure(
          lambda x: tf.cast(x, tf.float32), outputs)

      # Computes per-replica loss.
      loss = self.build_losses(
          model_outputs=outputs,
          labels=labels,
          aux_losses=model.losses)
      # Scales loss as the default gradients allreduce performs sum inside the
      # optimizer.
      scaled_loss = loss / num_replicas

      # For mixed_precision policy, when LossScaleOptimizer is used, loss is
      # scaled for numerical stability.
      if isinstance(
          optimizer, tf_keras.mixed_precision.LossScaleOptimizer):
        scaled_loss = optimizer.get_scaled_loss(scaled_loss)

    tvars = model.trainable_variables
    grads = tape.gradient(scaled_loss, tvars)
    # Scales back gradient before apply_gradients when LossScaleOptimizer is
    # used.
    if isinstance(
        optimizer, tf_keras.mixed_precision.LossScaleOptimizer):
      grads = optimizer.get_unscaled_gradients(grads)
    optimizer.apply_gradients(list(zip(grads, tvars)))

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
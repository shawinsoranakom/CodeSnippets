def train_step(self, inputs, model, optimizer, metrics=None):
    features, labels = inputs

    # To do a sanity check that we absolutely use no labels when pretraining, we
    # can set the labels here to zero.
    if self.task_config.train_data.input_set_label_to_zero:
      labels *= 0

    if (self.task_config.model.supervised_head is not None and
        self.task_config.evaluation.one_hot):
      num_classes = self.task_config.model.supervised_head.num_classes
      labels = tf.one_hot(labels, num_classes)

    num_replicas = tf.distribute.get_strategy().num_replicas_in_sync
    with tf.GradientTape() as tape:
      outputs = model(features, training=True)
      # Casting output layer as float32 is necessary when mixed_precision is
      # mixed_float16 or mixed_bfloat16 to ensure output is casted as float32.
      outputs = tf.nest.map_structure(lambda x: tf.cast(x, tf.float32), outputs)

      # Computes per-replica loss.
      losses = self.build_losses(
          model_outputs=outputs, labels=labels, aux_losses=model.losses)

      scaled_loss = losses['total_loss'] / num_replicas
      # For mixed_precision policy, when LossScaleOptimizer is used, loss is
      # scaled for numerical stability.
      if isinstance(optimizer, tf_keras.mixed_precision.LossScaleOptimizer):
        scaled_loss = optimizer.get_scaled_loss(scaled_loss)

    tvars = model.trainable_variables
    logging.info('Trainable variables:')
    for var in tvars:
      logging.info(var.name)
    grads = tape.gradient(scaled_loss, tvars)
    # Scales back gradient when LossScaleOptimizer is used.
    if isinstance(optimizer, tf_keras.mixed_precision.LossScaleOptimizer):
      grads = optimizer.get_unscaled_gradients(grads)
    optimizer.apply_gradients(list(zip(grads, tvars)))

    logs = {self.loss: losses['total_loss']}

    for m in metrics:
      m.update_state(losses[m.name])
      logs.update({m.name: m.result()})

    return logs
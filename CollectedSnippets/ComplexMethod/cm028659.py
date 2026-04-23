def train_step(self,
                 inputs: Tuple[Any, Any],
                 model: tf_keras.Model,
                 optimizer: tf_keras.optimizers.Optimizer,
                 metrics: Optional[List[Any]] = None) -> Dict[str, Any]:
    """Does forward and backward.

    Args:
      inputs: a dictionary of input tensors.
      model: the model, forward pass definition.
      optimizer: the optimizer for this training step.
      metrics: a nested structure of metrics objects.

    Returns:
      A dictionary of logs.
    """
    images, labels = inputs
    num_replicas = tf.distribute.get_strategy().num_replicas_in_sync

    with tf.GradientTape() as tape:
      model_kwargs = {
          'image_info': labels['image_info'],
          'anchor_boxes': labels['anchor_boxes'],
          'gt_boxes': labels['gt_boxes'],
          'gt_classes': labels['gt_classes'],
          'training': True,
      }
      if self.task_config.model.include_mask:
        model_kwargs['gt_masks'] = labels['gt_masks']
        if self.task_config.model.outer_boxes_scale > 1.0:
          model_kwargs['gt_outer_boxes'] = labels['gt_outer_boxes']
      outputs = model(images, **model_kwargs)
      outputs = tf.nest.map_structure(
          lambda x: tf.cast(x, tf.float32), outputs)

      # Computes per-replica loss.
      losses = self.build_losses(
          outputs=outputs, labels=labels, aux_losses=model.losses)
      scaled_loss = losses['total_loss'] / num_replicas

      # For mixed_precision policy, when LossScaleOptimizer is used, loss is
      # scaled for numerical stability.
      if isinstance(optimizer, tf_keras.mixed_precision.LossScaleOptimizer):
        scaled_loss = optimizer.get_scaled_loss(scaled_loss)

    tvars = model.trainable_variables
    grads = tape.gradient(scaled_loss, tvars)
    # Scales back gradient when LossScaleOptimizer is used.
    if isinstance(optimizer, tf_keras.mixed_precision.LossScaleOptimizer):
      grads = optimizer.get_unscaled_gradients(grads)
    optimizer.apply_gradients(list(zip(grads, tvars)))

    logs = {self.loss: losses['total_loss']}

    if metrics:
      for m in metrics:
        m.update_state(losses[m.name])

    if (self.task_config.segmentation_evaluation.report_train_mean_iou and
        self.segmentation_train_mean_iou is not None):
      segmentation_labels = {
          'masks': labels['gt_segmentation_mask'],
          'valid_masks': labels['gt_segmentation_valid_mask'],
          'image_info': labels['image_info']
      }
      self.process_metrics(
          metrics=[self.segmentation_train_mean_iou],
          labels=segmentation_labels,
          model_outputs=outputs['segmentation_outputs'])
      logs.update({
          self.segmentation_train_mean_iou.name:
              self.segmentation_train_mean_iou.result()
      })

    return logs
def build_model(self) -> tf_keras.Model:
    """Builds classification model with pruning."""
    model = super(ImageClassificationTask, self).build_model()
    if self.task_config.pruning is None:
      return model

    pruning_cfg = self.task_config.pruning

    prunable_model = tf_keras.models.clone_model(
        model,
        clone_function=self._make_block_prunable,
    )

    original_checkpoint = pruning_cfg.pretrained_original_checkpoint
    if original_checkpoint is not None:
      ckpt = tf.train.Checkpoint(model=prunable_model, **model.checkpoint_items)
      status = ckpt.read(original_checkpoint)
      status.expect_partial().assert_existing_objects_matched()

    pruning_params = {}
    if pruning_cfg.sparsity_m_by_n is not None:
      pruning_params['sparsity_m_by_n'] = pruning_cfg.sparsity_m_by_n

    if pruning_cfg.pruning_schedule == 'PolynomialDecay':
      pruning_params['pruning_schedule'] = tfmot.sparsity.keras.PolynomialDecay(
          initial_sparsity=pruning_cfg.initial_sparsity,
          final_sparsity=pruning_cfg.final_sparsity,
          begin_step=pruning_cfg.begin_step,
          end_step=pruning_cfg.end_step,
          frequency=pruning_cfg.frequency)
    elif pruning_cfg.pruning_schedule == 'ConstantSparsity':
      pruning_params[
          'pruning_schedule'] = tfmot.sparsity.keras.ConstantSparsity(
              target_sparsity=pruning_cfg.final_sparsity,
              begin_step=pruning_cfg.begin_step,
              frequency=pruning_cfg.frequency)
    else:
      raise NotImplementedError(
          'Only PolynomialDecay and ConstantSparsity are currently supported. Not support %s'
          % pruning_cfg.pruning_schedule)

    pruned_model = tfmot.sparsity.keras.prune_low_magnitude(
        prunable_model, **pruning_params)

    # Print out prunable weights for debugging purpose.
    prunable_layers = collect_prunable_layers(pruned_model)
    pruned_weights = []
    for layer in prunable_layers:
      pruned_weights += [weight.name for weight, _, _ in layer.pruning_vars]
    unpruned_weights = [
        weight.name
        for weight in pruned_model.weights
        if weight.name not in pruned_weights
    ]

    logging.info(
        '%d / %d weights are pruned.\nPruned weights: [ \n%s \n],\n'
        'Unpruned weights: [ \n%s \n],',
        len(pruned_weights), len(model.weights), ', '.join(pruned_weights),
        ', '.join(unpruned_weights))

    return pruned_model
def restore_map(self, fine_tune_checkpoint_type='lstm'):
    """Returns a map of variables to load from a foreign checkpoint.

    See parent class for details.

    Args:
      fine_tune_checkpoint_type: the type of checkpoint to restore from, either
        SSD/LSTM detection checkpoint (with compatible variable names)
        classification checkpoint for initialization prior to training.
        Available options: `classification`, `detection`, `interleaved`,
        and `lstm`.

    Returns:
      A dict mapping variable names (to load from a checkpoint) to variables in
      the model graph.
    Raises:
      ValueError: if fine_tune_checkpoint_type is not among
      `classification`/`detection`/`interleaved`/`lstm`.
    """
    if fine_tune_checkpoint_type not in [
        'classification', 'detection', 'interleaved', 'lstm',
        'interleaved_pretrain'
    ]:
      raise ValueError('Not supported fine_tune_checkpoint_type: {}'.format(
          fine_tune_checkpoint_type))

    self._restored_networks += 1
    base_network_scope = self.get_base_network_scope()
    if base_network_scope:
      scope_to_replace = '{0}_{1}'.format(base_network_scope,
                                          self._restored_networks)

    interleaved_model = False
    for variable in tf.global_variables():
      if scope_to_replace in variable.op.name:
        interleaved_model = True
        break

    variables_to_restore = {}
    for variable in tf.global_variables():
      var_name = variable.op.name
      if 'global_step' in var_name:
        continue

      # Remove FeatureExtractor prefix for classification checkpoints.
      if (fine_tune_checkpoint_type == 'classification' or
          fine_tune_checkpoint_type == 'interleaved_pretrain'):
        var_name = (
            re.split('^' + self._extract_features_scope + '/', var_name)[-1])

      # When loading from single frame detection checkpoints, we need to
      # remap FeatureMaps variable names.
      if ('FeatureMaps' in var_name and
          fine_tune_checkpoint_type == 'detection'):
        var_name = var_name.replace('FeatureMaps',
                                    self.get_base_network_scope())

      # Load interleaved checkpoint specifically.
      if interleaved_model:  # Interleaved LSTD.
        if 'interleaved' in fine_tune_checkpoint_type:
          variables_to_restore[var_name] = variable
        else:
          # Restore non-base layers from the first checkpoint only.
          if self._restored_networks == 1:
            if base_network_scope + '_' not in var_name:  # LSTM and FeatureMap
              variables_to_restore[var_name] = variable
          if scope_to_replace in var_name:
            var_name = var_name.replace(scope_to_replace, base_network_scope)
            variables_to_restore[var_name] = variable
      else:
        # Restore from the first model of interleaved checkpoints
        if 'interleaved' in fine_tune_checkpoint_type:
          var_name = var_name.replace(self.get_base_network_scope(),
                                      self.get_base_network_scope() + '_1', 1)

        variables_to_restore[var_name] = variable

    return variables_to_restore
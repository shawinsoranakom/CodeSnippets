def _build_assignment_map(keras_model,
                          prefix='',
                          skip_variables_regex=None,
                          var_to_shape_map=None):
  """Builds the variable assignment map.

  Compute an assignment mapping for loading older checkpoints into a Keras
  model. Variable names are remapped from the original TPUEstimator model to
  the new Keras name.

  Args:
    keras_model: tf_keras.Model object to provide variables to assign.
    prefix: prefix in the variable name to be remove for alignment with names in
      the checkpoint.
    skip_variables_regex: regular expression to math the names of variables that
      do not need to be assign.
    var_to_shape_map: variable name to shape mapping from the checkpoint.

  Returns:
    The variable assignment map.
  """
  assignment_map = {}

  checkpoint_names = []
  if var_to_shape_map:
    # pylint: disable=g-long-lambda
    checkpoint_names = list(
        filter(
            lambda x: not x.endswith('Momentum') and not x.endswith(
                'global_step'), var_to_shape_map.keys()))
    # pylint: enable=g-long-lambda

  logging.info('Number of variables in the checkpoint %d',
               len(checkpoint_names))

  for var in keras_model.variables:
    var_name = var.name

    if skip_variables_regex and re.match(skip_variables_regex, var_name):
      continue
    # Trim the index of the variable.
    if ':' in var_name:
      var_name = var_name[:var_name.rindex(':')]
    if var_name.startswith(prefix):
      var_name = var_name[len(prefix):]

    if not var_to_shape_map:
      assignment_map[var_name] = var
      continue

    # Match name with variables in the checkpoint.
    # pylint: disable=cell-var-from-loop
    match_names = list(filter(lambda x: x.endswith(var_name), checkpoint_names))
    # pylint: enable=cell-var-from-loop
    try:
      if match_names:
        assert len(match_names) == 1, 'more then on matches for {}: {}'.format(
            var_name, match_names)
        checkpoint_names.remove(match_names[0])
        assignment_map[match_names[0]] = var
      else:
        logging.info('Error not found var name: %s', var_name)
    except Exception as e:
      logging.info('Error removing the match_name: %s', match_names)
      logging.info('Exception: %s', e)
      raise
  logging.info('Found matching variable in checkpoint: %d', len(assignment_map))
  return assignment_map
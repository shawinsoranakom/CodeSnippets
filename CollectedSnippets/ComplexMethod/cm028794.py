def create_combine_fn(
    params: cfg.DataConfig
) -> Union[None, Callable[[tf.data.Dataset], tf.data.Dataset]]:
  """Creates and returns a combine_fn for dataset mixing."""
  if (
      hasattr(params, 'stop_on_empty_dataset')
      and params.stop_on_empty_dataset is not None
  ):
    stop_on_empty_dataset = params.stop_on_empty_dataset
  else:
    stop_on_empty_dataset = True

  if params.weights:
    # Combine multiple datasets using weighted sampling.
    if (not isinstance(params.input_path, cfg.base_config.Config) or
        not isinstance(params.weights, cfg.base_config.Config)):
      raise ValueError(
          'input_path and weights must both be a Config to use weighted '
          'sampling.')
    input_paths = params.input_path.as_dict()
    weights = params.weights.as_dict()
    if len(input_paths) != len(weights):
      raise ValueError(
          'The number of input_path and weights must be the same, but got %d '
          'input_paths and %d weights.' % (len(input_paths), len(weights)))

    for k in input_paths.keys():
      if k not in weights:
        raise ValueError(
            'input_path key \'%s\' does not have a corresponding weight.' % k)

    return build_weighted_sampling_combine_fn(weights, stop_on_empty_dataset)
  return None
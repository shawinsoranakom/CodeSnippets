def build(loss_config):
  """Build losses based on the config.

  Builds classification, localization losses and optionally a hard example miner
  based on the config.

  Args:
    loss_config: A losses_pb2.Loss object.

  Returns:
    classification_loss: Classification loss object.
    localization_loss: Localization loss object.
    classification_weight: Classification loss weight.
    localization_weight: Localization loss weight.
    hard_example_miner: Hard example miner object.
    random_example_sampler: BalancedPositiveNegativeSampler object.

  Raises:
    ValueError: If hard_example_miner is used with sigmoid_focal_loss.
    ValueError: If random_example_sampler is getting non-positive value as
      desired positive example fraction.
  """
  classification_loss = _build_classification_loss(
      loss_config.classification_loss)
  localization_loss = _build_localization_loss(
      loss_config.localization_loss)
  classification_weight = loss_config.classification_weight
  localization_weight = loss_config.localization_weight
  hard_example_miner = None
  if loss_config.HasField('hard_example_miner'):
    if (loss_config.classification_loss.WhichOneof('classification_loss') ==
        'weighted_sigmoid_focal'):
      raise ValueError('HardExampleMiner should not be used with sigmoid focal '
                       'loss')
    hard_example_miner = build_hard_example_miner(
        loss_config.hard_example_miner,
        classification_weight,
        localization_weight)
  random_example_sampler = None
  if loss_config.HasField('random_example_sampler'):
    if loss_config.random_example_sampler.positive_sample_fraction <= 0:
      raise ValueError('RandomExampleSampler should not use non-positive'
                       'value as positive sample fraction.')
    random_example_sampler = sampler.BalancedPositiveNegativeSampler(
        positive_fraction=loss_config.random_example_sampler.
        positive_sample_fraction)

  if loss_config.expected_loss_weights == loss_config.NONE:
    expected_loss_weights_fn = None
  elif loss_config.expected_loss_weights == loss_config.EXPECTED_SAMPLING:
    expected_loss_weights_fn = functools.partial(
        ops.expected_classification_loss_by_expected_sampling,
        min_num_negative_samples=loss_config.min_num_negative_samples,
        desired_negative_sampling_ratio=loss_config
        .desired_negative_sampling_ratio)
  elif (loss_config.expected_loss_weights == loss_config
        .REWEIGHTING_UNMATCHED_ANCHORS):
    expected_loss_weights_fn = functools.partial(
        ops.expected_classification_loss_by_reweighting_unmatched_anchors,
        min_num_negative_samples=loss_config.min_num_negative_samples,
        desired_negative_sampling_ratio=loss_config
        .desired_negative_sampling_ratio)
  else:
    raise ValueError('Not a valid value for expected_classification_loss.')

  return (classification_loss, localization_loss, classification_weight,
          localization_weight, hard_example_miner, random_example_sampler,
          expected_loss_weights_fn)
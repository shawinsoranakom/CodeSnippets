def _build_classification_loss(loss_config):
  """Builds a classification loss based on the loss config.

  Args:
    loss_config: A losses_pb2.ClassificationLoss object.

  Returns:
    Loss based on the config.

  Raises:
    ValueError: On invalid loss_config.
  """
  if not isinstance(loss_config, losses_pb2.ClassificationLoss):
    raise ValueError('loss_config not of type losses_pb2.ClassificationLoss.')

  loss_type = loss_config.WhichOneof('classification_loss')

  if loss_type == 'weighted_sigmoid':
    return losses.WeightedSigmoidClassificationLoss()

  elif loss_type == 'weighted_sigmoid_focal':
    config = loss_config.weighted_sigmoid_focal
    alpha = None
    if config.HasField('alpha'):
      alpha = config.alpha
    return losses.SigmoidFocalClassificationLoss(
        gamma=config.gamma,
        alpha=alpha)

  elif loss_type == 'weighted_softmax':
    config = loss_config.weighted_softmax
    return losses.WeightedSoftmaxClassificationLoss(
        logit_scale=config.logit_scale)

  elif loss_type == 'weighted_logits_softmax':
    config = loss_config.weighted_logits_softmax
    return losses.WeightedSoftmaxClassificationAgainstLogitsLoss(
        logit_scale=config.logit_scale)

  elif loss_type == 'bootstrapped_sigmoid':
    config = loss_config.bootstrapped_sigmoid
    return losses.BootstrappedSigmoidClassificationLoss(
        alpha=config.alpha,
        bootstrap_type=('hard' if config.hard_bootstrap else 'soft'))

  elif loss_type == 'penalty_reduced_logistic_focal_loss':
    config = loss_config.penalty_reduced_logistic_focal_loss
    return losses.PenaltyReducedLogisticFocalLoss(
        alpha=config.alpha, beta=config.beta)

  elif loss_type == 'weighted_dice_classification_loss':
    config = loss_config.weighted_dice_classification_loss
    return losses.WeightedDiceClassificationLoss(
        squared_normalization=config.squared_normalization,
        is_prediction_probability=config.is_prediction_probability)

  else:
    raise ValueError('Empty loss config.')
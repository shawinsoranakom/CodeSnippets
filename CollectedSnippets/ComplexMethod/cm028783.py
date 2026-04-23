def _create_model(
    *,
    bert_config: Optional[configs.BertConfig] = None,
    encoder_config: Optional[encoders.EncoderConfig] = None,
    with_mlm: bool,
) -> Tuple[tf_keras.Model, tf_keras.Model]:
  """Creates the model to export and the model to restore the checkpoint.

  Args:
    bert_config: A legacy `BertConfig` to create a `BertEncoder` object. Exactly
      one of encoder_config and bert_config must be set.
    encoder_config: An `EncoderConfig` to create an encoder of the configured
      type (`BertEncoder` or other).
    with_mlm: A bool to control the second component of the result. If True,
      will create a `BertPretrainerV2` object; otherwise, will create a
      `BertEncoder` object.

  Returns:
    A Tuple of (1) a Keras model that will be exported, (2) a `BertPretrainerV2`
    object or `BertEncoder` object depending on the value of `with_mlm`
    argument, which contains the first model and will be used for restoring
    weights from the checkpoint.
  """
  if (bert_config is not None) == (encoder_config is not None):
    raise ValueError("Exactly one of `bert_config` and `encoder_config` "
                     "can be specified, but got %s and %s" %
                     (bert_config, encoder_config))

  if bert_config is not None:
    encoder = get_bert_encoder(bert_config)
  else:
    encoder = encoders.build_encoder(encoder_config)

  # Convert from list of named inputs to dict of inputs keyed by name.
  # Only the latter accepts a dict of inputs after restoring from SavedModel.
  if isinstance(encoder.inputs, list) or isinstance(encoder.inputs, tuple):
    encoder_inputs_dict = {x.name: x for x in encoder.inputs}
  else:
    # encoder.inputs by default is dict for BertEncoderV2.
    encoder_inputs_dict = encoder.inputs
  encoder_output_dict = encoder(encoder_inputs_dict)
  # For interchangeability with other text representations,
  # add "default" as an alias for BERT's whole-input reptesentations.
  encoder_output_dict["default"] = encoder_output_dict["pooled_output"]
  core_model = tf_keras.Model(
      inputs=encoder_inputs_dict, outputs=encoder_output_dict)

  if with_mlm:
    if bert_config is not None:
      hidden_act = bert_config.hidden_act
    else:
      assert encoder_config is not None
      hidden_act = encoder_config.get().hidden_activation

    pretrainer = models.BertPretrainerV2(
        encoder_network=encoder,
        mlm_activation=tf_utils.get_activation(hidden_act))

    if isinstance(pretrainer.inputs, dict):
      pretrainer_inputs_dict = pretrainer.inputs
    else:
      pretrainer_inputs_dict = {x.name: x for x in pretrainer.inputs}
    pretrainer_output_dict = pretrainer(pretrainer_inputs_dict)
    mlm_model = tf_keras.Model(
        inputs=pretrainer_inputs_dict, outputs=pretrainer_output_dict)
    # Set `_auto_track_sub_layers` to False, so that the additional weights
    # from `mlm` sub-object will not be included in the core model.
    # TODO(b/169210253): Use a public API when available.
    core_model._auto_track_sub_layers = False  # pylint: disable=protected-access
    core_model.mlm = mlm_model
    return core_model, pretrainer
  else:
    return core_model, encoder
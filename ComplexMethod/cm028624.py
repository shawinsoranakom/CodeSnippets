def __init__(
      self,
      encoder_network: tf_keras.Model,
      mlm_activation=None,
      mlm_initializer='glorot_uniform',
      classification_heads: Optional[List[tf_keras.layers.Layer]] = None,
      customized_masked_lm: Optional[tf_keras.layers.Layer] = None,
      name: str = 'bert',
      **kwargs):

    inputs = copy.copy(encoder_network.inputs)
    outputs = {}
    encoder_network_outputs = encoder_network(inputs)
    if isinstance(encoder_network_outputs, list):
      outputs['pooled_output'] = encoder_network_outputs[1]
      if isinstance(encoder_network_outputs[0], list):
        outputs['encoder_outputs'] = encoder_network_outputs[0]
        outputs['sequence_output'] = encoder_network_outputs[0][-1]
      else:
        outputs['sequence_output'] = encoder_network_outputs[0]
    elif isinstance(encoder_network_outputs, dict):
      outputs = encoder_network_outputs
    else:
      raise ValueError('encoder_network\'s output should be either a list '
                       'or a dict, but got %s' % encoder_network_outputs)

    masked_lm_positions = tf_keras.layers.Input(
        shape=(None,), name='masked_lm_positions', dtype=tf.int32)
    inputs.append(masked_lm_positions)
    masked_lm_layer = customized_masked_lm or layers.MaskedLM(
        embedding_table=encoder_network.get_embedding_table(),
        activation=mlm_activation,
        initializer=mlm_initializer,
        name='cls/predictions')
    sequence_output = outputs['sequence_output']
    outputs['mlm_logits'] = masked_lm_layer(
        sequence_output, masked_positions=masked_lm_positions)

    classification_head_layers = classification_heads or []
    for cls_head in classification_head_layers:
      cls_outputs = cls_head(sequence_output)
      if isinstance(cls_outputs, dict):
        outputs.update(cls_outputs)
      else:
        outputs[cls_head.name] = cls_outputs

    super(MobileBERTEdgeTPUPretrainer, self).__init__(
        inputs=inputs,
        outputs=outputs,
        name=name,
        **kwargs)

    self._config = {
        'encoder_network': encoder_network,
        'mlm_activation': mlm_activation,
        'mlm_initializer': mlm_initializer,
        'classification_heads': classification_heads,
        'customized_masked_lm': customized_masked_lm,
        'name': name,
    }

    self.encoder_network = encoder_network
    self.masked_lm = masked_lm_layer
    self.classification_heads = classification_head_layers
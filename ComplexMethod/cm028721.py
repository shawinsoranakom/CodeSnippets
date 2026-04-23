def call(self, inputs):  # pytype: disable=signature-mismatch  # overriding-parameter-count-checks
    if isinstance(inputs, list):
      logging.warning('List inputs to BertPretrainer are discouraged.')
      inputs = dict([
          (ref.name, tensor) for ref, tensor in zip(self.inputs, inputs)
      ])

    outputs = dict()
    encoder_network_outputs = self.encoder_network(inputs)
    if isinstance(encoder_network_outputs, list):
      outputs['pooled_output'] = encoder_network_outputs[1]
      # When `encoder_network` was instantiated with return_all_encoder_outputs
      # set to True, `encoder_network_outputs[0]` is a list containing
      # all transformer layers' output.
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
    sequence_output = outputs['sequence_output']
    # Inference may not have masked_lm_positions and mlm_logits is not needed.
    if 'masked_lm_positions' in inputs:
      masked_lm_positions = inputs['masked_lm_positions']
      outputs['mlm_logits'] = self.masked_lm(
          sequence_output, masked_positions=masked_lm_positions)
    for cls_head in self.classification_heads:
      cls_outputs = cls_head(sequence_output)
      if isinstance(cls_outputs, dict):
        outputs.update(cls_outputs)
      else:
        outputs[cls_head.name] = cls_outputs
    return outputs
def __init__(self,
               network: tf_keras.Model,
               max_seq_length: int = 32,
               normalize: bool = True,
               logit_scale: float = 1.0,
               logit_margin: float = 0.0,
               output: str = 'logits',
               **kwargs) -> None:

    if output == 'logits':
      left_word_ids = tf_keras.layers.Input(
          shape=(max_seq_length,), dtype=tf.int32, name='left_word_ids')
      left_mask = tf_keras.layers.Input(
          shape=(max_seq_length,), dtype=tf.int32, name='left_mask')
      left_type_ids = tf_keras.layers.Input(
          shape=(max_seq_length,), dtype=tf.int32, name='left_type_ids')
    else:
      # Keep the consistant with legacy BERT hub module input names.
      left_word_ids = tf_keras.layers.Input(
          shape=(max_seq_length,), dtype=tf.int32, name='input_word_ids')
      left_mask = tf_keras.layers.Input(
          shape=(max_seq_length,), dtype=tf.int32, name='input_mask')
      left_type_ids = tf_keras.layers.Input(
          shape=(max_seq_length,), dtype=tf.int32, name='input_type_ids')

    left_inputs = [left_word_ids, left_mask, left_type_ids]
    left_outputs = network(left_inputs)
    if isinstance(left_outputs, list):
      left_sequence_output, left_encoded = left_outputs
    else:
      left_sequence_output = left_outputs['sequence_output']
      left_encoded = left_outputs['pooled_output']
    if normalize:
      left_encoded = tf_keras.layers.Lambda(
          lambda x: tf.nn.l2_normalize(x, axis=1))(
              left_encoded)

    if output == 'logits':
      right_word_ids = tf_keras.layers.Input(
          shape=(max_seq_length,), dtype=tf.int32, name='right_word_ids')
      right_mask = tf_keras.layers.Input(
          shape=(max_seq_length,), dtype=tf.int32, name='right_mask')
      right_type_ids = tf_keras.layers.Input(
          shape=(max_seq_length,), dtype=tf.int32, name='right_type_ids')

      right_inputs = [right_word_ids, right_mask, right_type_ids]
      right_outputs = network(right_inputs)
      if isinstance(right_outputs, list):
        _, right_encoded = right_outputs
      else:
        right_encoded = right_outputs['pooled_output']
      if normalize:
        right_encoded = tf_keras.layers.Lambda(
            lambda x: tf.nn.l2_normalize(x, axis=1))(
                right_encoded)

      dot_products = layers.MatMulWithMargin(
          logit_scale=logit_scale,
          logit_margin=logit_margin,
          name='dot_product')

      inputs = [
          left_word_ids, left_mask, left_type_ids, right_word_ids, right_mask,
          right_type_ids
      ]
      left_logits, right_logits = dot_products(left_encoded, right_encoded)

      outputs = dict(left_logits=left_logits, right_logits=right_logits)

    elif output == 'predictions':
      inputs = [left_word_ids, left_mask, left_type_ids]

      # To keep consistent with legacy BERT hub modules, the outputs are
      # "pooled_output" and "sequence_output".
      outputs = dict(
          sequence_output=left_sequence_output, pooled_output=left_encoded)
    else:
      raise ValueError('output type %s is not supported' % output)

    # b/164516224
    # Once we've created the network using the Functional API, we call
    # super().__init__ as though we were invoking the Functional API Model
    # constructor, resulting in this object having all the properties of a model
    # created using the Functional API. Once super().__init__ is called, we
    # can assign attributes to `self` - note that all `self` assignments are
    # below this line.
    super(DualEncoder, self).__init__(inputs=inputs, outputs=outputs, **kwargs)

    config_dict = {
        'network': network,
        'max_seq_length': max_seq_length,
        'normalize': normalize,
        'logit_scale': logit_scale,
        'logit_margin': logit_margin,
        'output': output,
    }
    # We are storing the config dict as a namedtuple here to ensure checkpoint
    # compatibility with an earlier version of this model which did not track
    # the config dict attribute. TF does not track immutable attrs which
    # do not contain Trackables, so by creating a config namedtuple instead of
    # a dict we avoid tracking it.
    config_cls = collections.namedtuple('Config', config_dict.keys())
    self._config = config_cls(**config_dict)

    self.network = network
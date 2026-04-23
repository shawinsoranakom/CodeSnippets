def __init__(self,
               encoder,
               decoder=None,
               mlm_activation=None,
               mlm_initializer='glorot_uniform',
               customized_masked_lm=None,
               name='pretrainer',
               **kwargs):
    """Init.

    Args:
      encoder:
        A perceiver encode and processor transformer network. It should expose
        its embedding table via a "get_embedding_table" method. Decoder won't
        be used if `sequence_output` is in the output of the encoder.
      decoder:
        A perceiver decoder network. This parameter is optional. This layer
        accepts the latent output of the encoder and emits logits. Decoder must
        accept a dictionary of `latent_output` and `input_mask` as inputs. This
        will not be used if `sequence_output` is an output from `encoder`.
      mlm_activation:
        The activation (if any) to use in the masked LM network. If `None`, no
        activation will be used.
      mlm_initializer:
        The initializer (if any) to use in the masked LM. Default
        to a Glorot uniform initializer.
      customized_masked_lm:
        A customized masked_lm layer. If None, will create
        a standard layer from `layers.MaskedLM`; if not None, will use the
        specified masked_lm layer. Above arguments `mlm_activation` and
        `mlm_initializer` will be ignored.
      name:
        Sets the `tf_keras.Model` name.
      **kwargs:
        Any keyword arguments to pass through to `tf_keras.Model`.
    """
    super().__init__(**kwargs, name=name)

    self._config = {
        'encoder': encoder,
        'decoder': decoder,
        'mlm_initializer': mlm_initializer,
        'mlm_activation': mlm_activation,
        'customized_masked_lm': customized_masked_lm,
        'name': name,
    }

    self._decoder = decoder
    self.encoder = encoder
    encoder_inputs = self.encoder.inputs

    # Makes sure the weights are built.
    encoder_outputs = self.encoder(encoder_inputs)

    if 'sequence_output' not in encoder_outputs:
      if 'latent_output' in encoder_outputs and self._decoder is not None:
        decoder_inputs = {
            'latent_output': encoder_outputs['latent_output'],
            'input_mask': encoder_inputs['input_mask'],
        }
        decoder_outputs = self._decoder(decoder_inputs)
        if 'sequence_output' not in decoder_outputs:
          raise ValueError('`sequence_output` must be in decoder output.')
      else:
        raise ValueError('if `sequence_output` is not in encoder output, '
                         '`latent_output` must be in encoder output and'
                         'decoder must exist.')

    encoder_inputs = copy.copy(self.encoder.inputs)
    inputs = dict(encoder_inputs)

    if self._decoder is not None:
      inputs.update(copy.copy(self._decoder.inputs))

    self.masked_lm = customized_masked_lm or layers.MaskedLM(
        embedding_table=self.encoder.get_embedding_table(),
        activation=mlm_activation,
        initializer=mlm_initializer,
        name='cls/predictions')
    masked_lm_positions = tf_keras.layers.Input(
        shape=(None,), name='masked_lm_positions', dtype=tf.int32)

    if isinstance(inputs, dict):
      inputs['masked_lm_positions'] = masked_lm_positions
    else:
      raise ValueError(f'Unexpected inputs type to {self.__class__}.')
    self.inputs = inputs
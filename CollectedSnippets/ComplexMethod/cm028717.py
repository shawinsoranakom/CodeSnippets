def __call__(self,
               inputs=None,
               encoder_mask=None,
               dense_inputs=None,
               training=False):
    """Applies Transformer model on the inputs.

    Args:
      inputs: input word ids. Optional if dense data are provided.
      encoder_mask: the encoder self-attention mask.
      dense_inputs: dense input data. Concat after the embedding if word ids are
        provided.
      training: whether it is training pass, affecting dropouts.

    Returns:
      output of a transformer encoder.
    """
    # Casts inputs to the dtype.
    if encoder_mask is not None:
      encoder_mask = tf.cast(encoder_mask, self.compute_dtype)
    cfg = self.config
    inputs_array = []
    if inputs is not None:
      inputs_array.append(
          self.input_embed(inputs, one_hot=cfg.one_hot_embedding))
    if dense_inputs is not None:
      inputs_array.append(dense_inputs)
    if not inputs_array:
      raise ValueError("At least one of inputs and dense_inputs must not be "
                       "None.")
    x = tf.concat(inputs_array, axis=1)
    tensor_shape = tf_utils.get_shape_list(x)
    tensor_shape[-2] = 1
    x = self.input_dropout(x, noise_shape=tensor_shape, training=training)
    if inputs is not None:
      input_length = tf_utils.get_shape_list(inputs)[1]
    else:
      input_length = 0

    attention_outputs = []
    for i in range(cfg.num_layers):
      position_bias = self.get_relpos_bias(input_length, dense_inputs, i)
      x = self.encoder_layers[i](
          x,
          attention_mask=encoder_mask,
          position_bias=position_bias,
          training=training)
      if self.config.return_attention_scores:
        x, attention_scores = x
        attention_outputs.append(attention_scores)

    encoded = self.output_norm(x)
    encoded = self.output_dropout(encoded, training=training)
    if self.config.return_attention_scores:
      return encoded, attention_outputs
    else:
      return encoded
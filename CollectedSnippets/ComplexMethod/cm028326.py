def _compute_box_context_attention(box_features, num_proposals,
                                   context_features, valid_context_size,
                                   bottleneck_dimension,
                                   attention_temperature, is_training,
                                   max_num_proposals,
                                   use_self_attention=False,
                                   use_long_term_attention=True,
                                   self_attention_in_sequence=False,
                                   num_attention_heads=1,
                                   num_attention_layers=1):
  """Computes the attention feature from the context given a batch of box.

  Args:
    box_features: A float Tensor of shape [batch_size * max_num_proposals,
      height, width, channels]. It is pooled features from first stage
      proposals.
    num_proposals: The number of valid box proposals.
    context_features: A float Tensor of shape [batch_size, context_size,
      num_context_features].
    valid_context_size: A int32 Tensor of shape [batch_size].
    bottleneck_dimension: A int32 Tensor representing the bottleneck dimension
      for intermediate projections.
    attention_temperature: A float Tensor. It controls the temperature of the
      softmax for weights calculation. The formula for calculation as follows:
        weights = exp(weights / temperature) / sum(exp(weights / temperature))
    is_training: A boolean Tensor (affecting batch normalization).
    max_num_proposals: The number of box proposals for each image.
    use_self_attention: Whether to use an attention block across the
      first stage predicted box features for the input image.
    use_long_term_attention: Whether to use an attention block into the context
      features.
    self_attention_in_sequence: Whether self-attention and long term attention
      should be in sequence or parallel.
    num_attention_heads: Number of heads for multi-headed attention.
    num_attention_layers: Number of heads for multi-layered attention.

  Returns:
    A float Tensor of shape [batch_size, max_num_proposals, 1, 1, channels].
  """
  _, context_size, _ = context_features.shape
  context_valid_mask = compute_valid_mask(valid_context_size, context_size)

  total_proposals, height, width, channels = box_features.shape

  batch_size = total_proposals // max_num_proposals
  box_features = tf.reshape(
      box_features,
      [batch_size,
       max_num_proposals,
       height,
       width,
       channels])

  # Average pools over height and width dimension so that the shape of
  # box_features becomes [batch_size, max_num_proposals, channels].
  box_features = tf.reduce_mean(box_features, [2, 3])
  box_valid_mask = compute_valid_mask(
      num_proposals,
      box_features.shape[1])

  if use_self_attention:
    self_attention_box_features = attention_block(
        box_features, box_features, bottleneck_dimension, channels.value,
        attention_temperature, keys_values_valid_mask=box_valid_mask,
        queries_valid_mask=box_valid_mask, is_training=is_training,
        block_name="SelfAttentionBlock")

  if use_long_term_attention:
    if use_self_attention and self_attention_in_sequence:
      input_features = tf.add(self_attention_box_features, box_features)
      input_features = tf.divide(input_features, 2)
    else:
      input_features = box_features
    original_input_features = input_features
    for jdx in range(num_attention_layers):
      layer_features = tf.zeros_like(input_features)
      for idx in range(num_attention_heads):
        block_name = "AttentionBlock" + str(idx) + "_AttentionLayer" +str(jdx)
        attention_features = attention_block(
            input_features,
            context_features,
            bottleneck_dimension,
            channels.value,
            attention_temperature,
            keys_values_valid_mask=context_valid_mask,
            queries_valid_mask=box_valid_mask,
            is_training=is_training,
            block_name=block_name)
        layer_features = tf.add(layer_features, attention_features)
      layer_features = tf.divide(layer_features, num_attention_heads)
      input_features = tf.add(input_features, layer_features)
    output_features = tf.add(input_features, original_input_features)
    if not self_attention_in_sequence and use_self_attention:
      output_features = tf.add(self_attention_box_features, output_features)
  elif use_self_attention:
    output_features = self_attention_box_features
  else:
    output_features = tf.zeros(self_attention_box_features.shape)

  # Expands the dimension back to match with the original feature map.
  output_features = output_features[:, :, tf.newaxis, tf.newaxis, :]

  return output_features
def decode(
      self,
      encoded,
      decoder_target_tokens,
      encoder_input_tokens=None,  # only used for masks
      encoder_dense_inputs=None,
      decoder_input_tokens=None,
      encoder_segment_ids=None,
      encoder_dense_segment_ids=None,
      decoder_segment_ids=None,
      decode_position=None,
      cache=None,
      max_decode_len=None,
      decode=False,
      training=False) -> Dict[str, tf.Tensor]:
    eligible_inputs_array = []
    if encoder_input_tokens is not None:
      eligible_inputs = tf.cast(
          tf.not_equal(encoder_input_tokens, 0), self.compute_dtype)
      eligible_inputs_array.append(eligible_inputs)
    if encoder_dense_inputs is not None:
      eligible_dense_inputs = tf.cast(
          tf.reduce_any(tf.not_equal(encoder_dense_inputs, 0), axis=-1),
          self.compute_dtype)
      eligible_inputs_array.append(eligible_dense_inputs)
    eligible_inputs = tf.concat(eligible_inputs_array, axis=1)

    if decode:
      # For decoding, the decoder_input_tokens is the decoder_target_tokens.
      decoder_input_tokens = decoder_target_tokens
      # fast autoregressive decoding uses only a special encoder-decoder mask
      decoder_mask = None
      encoder_decoder_mask = make_attention_mask(
          tf.cast(
              tf.not_equal(tf.ones_like(decoder_target_tokens), 0),
              self.compute_dtype),
          eligible_inputs,
          dtype=tf.bool)
    else:
      # Note that, masks should be created using decoder_target_tokens.
      eligible_targets = tf.cast(
          tf.not_equal(decoder_target_tokens, 0), self.compute_dtype)
      decoder_mask = tf.math.logical_and(
          make_attention_mask(
              eligible_targets, eligible_targets, dtype=tf.bool),
          make_causal_mask(decoder_target_tokens, dtype=tf.bool))
      encoder_decoder_mask = make_attention_mask(
          eligible_targets, eligible_inputs, dtype=tf.bool)
      if encoder_segment_ids is not None:
        if decoder_mask is not None:
          decoder_mask = tf.math.logical_and(
              decoder_mask,
              make_attention_mask(
                  decoder_segment_ids,
                  decoder_segment_ids,
                  tf.equal,
                  dtype=tf.bool))
        if encoder_dense_segment_ids is not None:
          encoder_segment_ids = tf.concat(
              [encoder_segment_ids, encoder_dense_segment_ids], axis=1)
        encoder_decoder_mask = tf.math.logical_and(
            encoder_decoder_mask,
            make_attention_mask(
                decoder_segment_ids,
                encoder_segment_ids,
                tf.equal,
                dtype=tf.bool))
    if decoder_mask is not None:
      decoder_mask = (1.0 - tf.cast(decoder_mask, self.compute_dtype)) * -1e9
    encoder_decoder_mask = (
        1.0 - tf.cast(encoder_decoder_mask, self.compute_dtype)) * -1e9
    outputs = self.decoder(
        decoder_input_tokens,
        encoded,
        decode_position=decode_position,
        decoder_mask=decoder_mask,
        encoder_decoder_mask=encoder_decoder_mask,
        cache=cache,
        max_decode_len=max_decode_len,
        decode=decode,
        training=training)
    outputs["encoded"] = encoded
    return outputs
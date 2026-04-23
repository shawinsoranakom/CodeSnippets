def call(self, inputs: Any) -> Any:
    """MEGA encoder block call.

    Args:
      inputs: a single tensor or a list of tensors. `input tensor`
        as the single sequence of embeddings. [`input tensor`,
        `attention mask`] to have the
        additional attention mask. [`query tensor`, `key value tensor`,
        `attention mask`] to have separate input streams for the query, and
        key/value to the multi-head attention.
    Returns:
      An output tensor with the same dimensions as input/query tensor.
    """
    if isinstance(inputs, (list, tuple)):
      if len(inputs) == 2:
        (input_tensor, attention_mask) = inputs
        key_value = None
      elif len(inputs) == 3:
        (input_tensor, key_value, attention_mask) = inputs
      else:
        raise ValueError(
            "Unexpected inputs to %s with length at %d"
            % (self.__class__, len(inputs))
        )
    else:
      (input_tensor, key_value, attention_mask) = (inputs, None, None)

    if self.prenorm:
      input_tensor = self.norm(input_tensor)
      if key_value is not None:
        key_value = self.norm(key_value)

    ## B*L*D -> L*B*D
    ## Multi-Dimensional Damped EMA
    x = tf.transpose(input_tensor, perm=[1, 0, 2])
    residual = x

    seq_len, bsz, _ = x.shape

    # L x B x E
    v = self.activation(self.v_proj(x))

    # L x B x D
    mx = self.move(x, attention_mask)
    mx = self.dropout(mx)

    # L x B x D -> L x B x (2*D+S+E)
    base = self.mx_proj(mx)

    u, zr, hx = tf.split(
        base, [self.embed_dim, self.zdim + self.hdim, self.embed_dim], axis=-1
    )
    # L x B x D
    u = tf.math.sigmoid(u)
    # L x B x (E+S)
    z, r = tf.split(tf.nn.silu(zr), [self.zdim, self.hdim], axis=-1)
    # L x B x S -> L x B x 1 x S -> L x B x 2 x S
    z = tf.expand_dims(z, axis=2) * self.gamma + self.beta
    # L x B x 2 x S -> L x B x S
    q, k = tf.unstack(z, axis=2)

    # L x B x D -> B x L x D
    q = tf.transpose(q, perm=(1, 0, 2))
    k = tf.transpose(k, perm=(1, 0, 2))
    # L x B x E -> B x L x E
    v = tf.transpose(v, perm=(1, 0, 2))

    attn_weights = self._softmax_attention(q, k)
    v = self.hidden_dropout(v)
    kernel = tf.squeeze(self.attention_dropout(attn_weights))
    # B x K x C x E -> B x L x E -> L x B x E
    h = tf.transpose(
        tf.reshape(
            tf.linalg.matmul(kernel, v), shape=(bsz, seq_len, self.hdim)
        ),
        perm=(1, 0, 2),
    )

    # L x B x E -> L x B x D
    h = self.activation(hx + self.h_proj(h * r))
    h = self.dropout(h)
    # L x B x D
    out = residual + tf.math.multiply(u, h - residual)

    if not self.prenorm:
      out = self.norm(out)

    out = tf.transpose(out, perm=(1, 0, 2))

    if self.prenorm:
      out = self.ffn_norm(out)

    inner_output = self._intermediate_dense(out)
    inner_output = self._intermediate_activation_layer(inner_output)
    inner_output = self.ffn_intermediate_dropout(inner_output)
    layer_output = self._output_dense(inner_output)
    layer_output = self.output_dropout(layer_output) + out

    if not self.prenorm:
      layer_output = self.ffn_norm(layer_output)

    return layer_output
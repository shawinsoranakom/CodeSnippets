def fuse_features(self, nodes):
    """Fuses features from different resolutions and return a weighted sum.

    Args:
      nodes: a list of tensorflow features at different levels

    Returns:
      A tensor denoting the fused feature.
    """
    dtype = nodes[0].dtype

    if self.weight_method == 'attn':
      edge_weights = [tf.cast(var, dtype=dtype) for var in self.vars]
      normalized_weights = tf.nn.softmax(tf.stack(edge_weights))
      nodes = tf.stack(nodes, axis=-1)
      new_node = tf.reduce_sum(nodes * normalized_weights, -1)
    elif self.weight_method == 'fastattn':
      edge_weights = [
          tf.nn.relu(tf.cast(var, dtype=dtype)) for var in self.vars
      ]
      weights_sum = add_n(edge_weights)
      nodes = [
          nodes[i] * edge_weights[i] / (weights_sum + 0.0001)
          for i in range(len(nodes))
      ]
      new_node = add_n(nodes)
    elif self.weight_method == 'channel_attn':
      edge_weights = [tf.cast(var, dtype=dtype) for var in self.vars]
      normalized_weights = tf.nn.softmax(tf.stack(edge_weights, -1), axis=-1)
      nodes = tf.stack(nodes, axis=-1)
      new_node = tf.reduce_sum(nodes * normalized_weights, -1)
    elif self.weight_method == 'channel_fastattn':
      edge_weights = [
          tf.nn.relu(tf.cast(var, dtype=dtype)) for var in self.vars
      ]
      weights_sum = add_n(edge_weights)
      nodes = [
          nodes[i] * edge_weights[i] / (weights_sum + 0.0001)
          for i in range(len(nodes))
      ]
      new_node = add_n(nodes)
    elif self.weight_method == 'sum':
      new_node = add_n(nodes)
    else:
      raise ValueError('unknown weight_method %s' % self.weight_method)

    return new_node
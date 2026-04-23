def _spaghetti_node(self, node, scope):
    """Spaghetti node."""
    node_spec = self._node_specs.nodes[node]

    # Make spaghetti edges
    edge_outputs = []
    edge_min_level = 100  # Currently we don't have any level over 7.
    edge_output_shape = None
    for edge in node_spec.edges:
      if isinstance(edge, SpaghettiPassthroughEdge):
        assert len(node_spec.edges) == 1, len(node_spec.edges)
        edge_outputs.append(self._nodes[edge.input])
      elif isinstance(edge, SpaghettiResampleEdge):
        edge_outputs.append(
            self._spaghetti_edge(node, edge.input,
                                 'edge_{}_{}'.format(edge.input, node)))
        if edge_min_level > self._node_specs.nodes[edge.input].level:
          edge_min_level = self._node_specs.nodes[edge.input].level
          edge_output_shape = tf.shape(edge_outputs[-1])
      else:
        raise ValueError('Unknown edge type {}'.format(edge))

    if len(edge_outputs) == 1:
      # When edge_outputs' length is 1, it is passthrough edge.
      net = edge_outputs[-1]
    else:
      # When edge_outputs' length is over 1, need to crop and then add edges.
      net = edge_outputs[0][:, :edge_output_shape[1], :edge_output_shape[2], :]
      for edge_output in edge_outputs[1:]:
        net += edge_output[:, :edge_output_shape[1], :edge_output_shape[2], :]
      net = self._activation_fn(net)

    # Make spaghetti node
    for idx, layer_spec in enumerate(node_spec.layers):
      if isinstance(layer_spec, IbnOp):
        net_exp = self._expanded_conv(net, node_spec.num_filters,
                                      layer_spec.expansion_rate,
                                      layer_spec.kernel_size, layer_spec.stride,
                                      '{}_{}'.format(scope, idx))
      elif isinstance(layer_spec, IbnFusedGrouped):
        net_exp = self._ibn_fused_grouped(net, node_spec.num_filters,
                                          layer_spec.expansion_rate,
                                          layer_spec.kernel_size,
                                          layer_spec.stride, layer_spec.groups,
                                          '{}_{}'.format(scope, idx))
      elif isinstance(layer_spec, SepConvOp):
        net_exp = self._sep_conv(net, node_spec.num_filters,
                                 layer_spec.kernel_size, layer_spec.stride,
                                 '{}_{}'.format(scope, idx))
      else:
        raise ValueError('Unsupported layer_spec: {}'.format(layer_spec))
      # Skip connection for all layers other than the first in a node.
      net = net_exp + net if layer_spec.has_residual else net_exp
    self._nodes[node] = net
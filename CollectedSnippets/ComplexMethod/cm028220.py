def call(self, feature_pyramid):
    """Compute BiFPN feature maps from input feature pyramid.

    Executed when calling the `.__call__` method on input.

    Args:
      feature_pyramid: list of tuples of (tensor_name, image_feature_tensor).

    Returns:
      feature_maps: an OrderedDict mapping keys (feature map names) to
        tensors where each tensor has shape [batch, height_i, width_i, depth_i].
    """
    feature_maps = [el[1] for el in feature_pyramid]
    output_feature_maps = [None for node in self.bifpn_output_node_names]

    for index, node in enumerate(self.bifpn_node_config):
      node_scope = 'node_{:02d}'.format(index)
      with tf.name_scope(node_scope):
        # Apply layer blocks to this node's input feature maps.
        input_block_results = []
        for input_index, input_block in self.node_input_blocks[index]:
          block_result = feature_maps[input_index]
          for layer in input_block:
            block_result = layer(block_result)
          input_block_results.append(block_result)

        # Combine the resulting feature maps.
        node_result = self.node_combine_op[index](input_block_results)

        # Apply post-combine layer block if applicable.
        for layer in self.node_post_combine_block[index]:
          node_result = layer(node_result)

        feature_maps.append(node_result)

        if node['name'] in self.bifpn_output_node_names:
          index = self.bifpn_output_node_names.index(node['name'])
          output_feature_maps[index] = node_result

    return collections.OrderedDict(
        zip(self.bifpn_output_node_names, output_feature_maps))
def _build_feature_pyramid(self, feats):
    num_output_connections = [0] * len(feats)
    num_output_levels = self._max_level - self._min_level + 1
    feat_levels = list(range(self._min_level, self._max_level + 1))

    for i, block_spec in enumerate(self._block_specs):
      new_level = block_spec.level

      # Checks the range of input_offsets.
      for input_offset in block_spec.input_offsets:
        if input_offset >= len(feats):
          raise ValueError(
              'input_offset ({}) is larger than num feats({})'.format(
                  input_offset, len(feats)))
      input0 = block_spec.input_offsets[0]
      input1 = block_spec.input_offsets[1]

      # Update graph with inputs.
      node0 = feats[input0]
      node0_level = feat_levels[input0]
      num_output_connections[input0] += 1
      node0 = self._resample_feature_map(node0, node0_level, new_level)
      node1 = feats[input1]
      node1_level = feat_levels[input1]
      num_output_connections[input1] += 1
      node1 = self._resample_feature_map(node1, node1_level, new_level)

      # Combine node0 and node1 to create new feat.
      if block_spec.combine_fn == 'sum':
        new_node = node0 + node1
      elif block_spec.combine_fn == 'attention':
        if node0_level >= node1_level:
          new_node = self._global_attention(node0, node1)
        else:
          new_node = self._global_attention(node1, node0)
      else:
        raise ValueError('unknown combine_fn `{}`.'
                         .format(block_spec.combine_fn))

      # Add intermediate nodes that do not have any connections to output.
      if block_spec.is_output:
        for j, (feat, feat_level, num_output) in enumerate(
            zip(feats, feat_levels, num_output_connections)):
          if num_output == 0 and feat_level == new_level:
            num_output_connections[j] += 1

            feat_ = self._resample_feature_map(feat, feat_level, new_level)
            new_node += feat_

      new_node = self._activation(new_node)
      new_node = self._conv_op(
          filters=self._config_dict['num_filters'],
          kernel_size=(3, 3),
          padding='same',
          **self._conv_kwargs)(new_node)
      new_node = self._norm_op(**self._norm_kwargs)(new_node)

      feats.append(new_node)
      feat_levels.append(new_level)
      num_output_connections.append(0)

    output_feats = {}
    for i in range(len(feats) - num_output_levels, len(feats)):
      level = feat_levels[i]
      output_feats[level] = feats[i]
    logging.info('Output feature pyramid: %s', output_feats)
    return output_feats
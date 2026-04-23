def _build_scale_permuted_network(self,
                                    net,
                                    input_width,
                                    weighted_fusion=False):
    """Builds scale-permuted network."""
    net_sizes = [int(math.ceil(input_width / 2**2))] * len(net)
    net_block_fns = [self._init_block_fn] * len(net)
    num_outgoing_connections = [0] * len(net)

    endpoints = {}
    for i, block_spec in enumerate(self._block_specs):
      # Find out specs for the target block.
      target_width = int(math.ceil(input_width / 2**block_spec.level))
      target_num_filters = int(FILTER_SIZE_MAP[block_spec.level] *
                               self._filter_size_scale)
      target_block_fn = block_spec.block_fn

      # Resample then merge input0 and input1.
      parents = []
      input0 = block_spec.input_offsets[0]
      input1 = block_spec.input_offsets[1]

      x0 = self._resample_with_alpha(
          inputs=net[input0],
          input_width=net_sizes[input0],
          input_block_fn=net_block_fns[input0],
          target_width=target_width,
          target_num_filters=target_num_filters,
          target_block_fn=target_block_fn,
          alpha=self._resample_alpha)
      parents.append(x0)
      num_outgoing_connections[input0] += 1

      x1 = self._resample_with_alpha(
          inputs=net[input1],
          input_width=net_sizes[input1],
          input_block_fn=net_block_fns[input1],
          target_width=target_width,
          target_num_filters=target_num_filters,
          target_block_fn=target_block_fn,
          alpha=self._resample_alpha)
      parents.append(x1)
      num_outgoing_connections[input1] += 1

      # Merge 0 outdegree blocks to the output block.
      if block_spec.is_output:
        for j, (j_feat,
                j_connections) in enumerate(zip(net, num_outgoing_connections)):
          if j_connections == 0 and (j_feat.shape[2] == target_width and
                                     j_feat.shape[3] == x0.shape[3]):
            parents.append(j_feat)
            num_outgoing_connections[j] += 1

      # pylint: disable=g-direct-tensorflow-import
      if weighted_fusion:
        dtype = parents[0].dtype
        parent_weights = [
            tf.nn.relu(tf.cast(tf.Variable(1.0, name='block{}_fusion{}'.format(
                i, j)), dtype=dtype)) for j in range(len(parents))]
        weights_sum = tf.add_n(parent_weights)
        parents = [
            parents[i] * parent_weights[i] / (weights_sum + 0.0001)
            for i in range(len(parents))
        ]

      # Fuse all parent nodes then build a new block.
      x = tf_utils.get_activation(self._activation_fn)(tf.add_n(parents))
      x = self._block_group(
          inputs=x,
          filters=target_num_filters,
          strides=1,
          block_fn_cand=target_block_fn,
          block_repeats=self._block_repeats,
          stochastic_depth_drop_rate=nn_layers.get_stochastic_depth_rate(
              self._init_stochastic_depth_rate, i + 1, len(self._block_specs)),
          name='scale_permuted_block_{}'.format(i + 1))

      net.append(x)
      net_sizes.append(target_width)
      net_block_fns.append(target_block_fn)
      num_outgoing_connections.append(0)

      # Save output feats.
      if block_spec.is_output:
        if block_spec.level in endpoints:
          raise ValueError('Duplicate feats found for output level {}.'.format(
              block_spec.level))
        if (block_spec.level < self._min_level or
            block_spec.level > self._max_level):
          logging.warning(
              'SpineNet output level %s out of range [min_level, max_level] = '
              '[%s, %s] will not be used for further processing.',
              block_spec.level, self._min_level, self._max_level)
        endpoints[str(block_spec.level)] = x

    return endpoints
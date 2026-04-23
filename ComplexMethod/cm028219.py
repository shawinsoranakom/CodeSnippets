def _create_bifpn_node_config(bifpn_num_iterations,
                              bifpn_num_filters,
                              fpn_min_level,
                              fpn_max_level,
                              input_max_level,
                              bifpn_node_params=None,
                              level_scales=None,
                              use_native_resize_op=False):
  """Creates a config specifying a bidirectional feature pyramid network.

  Args:
    bifpn_num_iterations: the number of top-down bottom-up feature computations
      to repeat in the BiFPN.
    bifpn_num_filters: the number of filters (channels) for every feature map
      used in the BiFPN.
    fpn_min_level: the minimum pyramid level (highest feature map resolution) to
      use in the BiFPN.
    fpn_max_level: the maximum pyramid level (lowest feature map resolution) to
      use in the BiFPN.
    input_max_level: the maximum pyramid level that will be provided as input to
      the BiFPN. Accordingly, the BiFPN will compute additional pyramid levels
      from input_max_level, up to the desired fpn_max_level.
    bifpn_node_params: If not 'None', a dictionary of additional default BiFPN
      node parameters that will be applied to all BiFPN nodes.
    level_scales: a list of pyramid level scale factors. If 'None', each level's
      scale is set to 2^level by default, which corresponds to each successive
      feature map scaling by a factor of 2.
    use_native_resize_op: If true, will use
      tf.compat.v1.image.resize_nearest_neighbor for unsampling.

  Returns:
    A list of dictionaries used to define nodes in the BiFPN computation graph,
    as proposed by EfficientDet, Tan et al (https://arxiv.org/abs/1911.09070).
    Each node's entry has the corresponding keys:
      name: String. The name of this node in the BiFPN. The node name follows
        the format '{bifpn_iteration}_{dn|up}_lvl_{pyramid_level}', where 'dn'
        or 'up' refers to whether the node is in the top-down or bottom-up
        portion of a single BiFPN iteration.
      scale: the scale factor for this node, by default 2^level.
      inputs: A list of names of nodes which are inputs to this node.
      num_channels: The number of channels for this node.
      combine_method: String. Name of the method used to combine input
        node feature maps, 'fast_attention' by default for nodes which have more
        than one input. Otherwise, 'None' for nodes with only one input node.
      input_op: A (partial) function which is called to construct the layers
        that will be applied to this BiFPN node's inputs. This function is
        called with the arguments:
          input_op(name, input_scale, input_num_channels, output_scale,
                   output_num_channels, conv_hyperparams, is_training,
                   freeze_batchnorm)
      post_combine_op: A (partial) function which is called to construct the
        layers that will be applied to the result of the combine operation for
        this BiFPN node. This function will be called with the arguments:
          post_combine_op(name, conv_hyperparams, is_training, freeze_batchnorm)
        If 'None', then no layers will be applied after the combine operation
        for this node.
  """
  if not level_scales:
    level_scales = [2**i for i in range(fpn_min_level, fpn_max_level + 1)]

  default_node_params = {
      'num_channels':
          bifpn_num_filters,
      'combine_method':
          'fast_attention',
      'input_op':
          functools.partial(
              _create_bifpn_resample_block,
              downsample_method='max_pooling',
              use_native_resize_op=use_native_resize_op),
      'post_combine_op':
          functools.partial(
              bifpn_utils.create_conv_block,
              num_filters=bifpn_num_filters,
              kernel_size=3,
              strides=1,
              padding='SAME',
              use_separable=True,
              apply_batchnorm=True,
              apply_activation=True,
              conv_bn_act_pattern=False),
  }
  if bifpn_node_params:
    default_node_params.update(bifpn_node_params)

  bifpn_node_params = []
  # Create additional base pyramid levels not provided as input to the BiFPN.
  # Note, combine_method and post_combine_op are set to None for additional
  # base pyramid levels because they do not combine multiple input BiFPN nodes.
  for i in range(input_max_level + 1, fpn_max_level + 1):
    node_params = dict(default_node_params)
    node_params.update({
        'name': '0_up_lvl_{}'.format(i),
        'scale': level_scales[i - fpn_min_level],
        'inputs': ['0_up_lvl_{}'.format(i - 1)],
        'combine_method': None,
        'post_combine_op': None,
    })
    bifpn_node_params.append(node_params)

  for i in range(bifpn_num_iterations):
    # The first bottom-up feature pyramid (which includes the input pyramid
    # levels from the backbone network and the additional base pyramid levels)
    # is indexed at 0. So, the first top-down bottom-up pass of the BiFPN is
    # indexed from 1, and repeated for bifpn_num_iterations iterations.
    bifpn_i = i + 1

    # Create top-down nodes.
    for level_i in reversed(range(fpn_min_level, fpn_max_level)):
      inputs = []
      # BiFPN nodes in the top-down pass receive input from the corresponding
      # level from the previous BiFPN iteration's bottom-up pass, except for the
      # bottom-most (min) level node, which is computed once in the initial
      # bottom-up pass, and is afterwards only computed in each top-down pass.
      if level_i > fpn_min_level or bifpn_i == 1:
        inputs.append('{}_up_lvl_{}'.format(bifpn_i - 1, level_i))
      else:
        inputs.append('{}_dn_lvl_{}'.format(bifpn_i - 1, level_i))
      inputs.append(bifpn_node_params[-1]['name'])
      node_params = dict(default_node_params)
      node_params.update({
          'name': '{}_dn_lvl_{}'.format(bifpn_i, level_i),
          'scale': level_scales[level_i - fpn_min_level],
          'inputs': inputs
      })
      bifpn_node_params.append(node_params)

    # Create bottom-up nodes.
    for level_i in range(fpn_min_level + 1, fpn_max_level + 1):
      # BiFPN nodes in the bottom-up pass receive input from the corresponding
      # level from the preceding top-down pass, except for the top (max) level
      # which does not have a corresponding node in the top-down pass.
      inputs = ['{}_up_lvl_{}'.format(bifpn_i - 1, level_i)]
      if level_i < fpn_max_level:
        inputs.append('{}_dn_lvl_{}'.format(bifpn_i, level_i))
      inputs.append(bifpn_node_params[-1]['name'])
      node_params = dict(default_node_params)
      node_params.update({
          'name': '{}_up_lvl_{}'.format(bifpn_i, level_i),
          'scale': level_scales[level_i - fpn_min_level],
          'inputs': inputs
      })
      bifpn_node_params.append(node_params)

  return bifpn_node_params
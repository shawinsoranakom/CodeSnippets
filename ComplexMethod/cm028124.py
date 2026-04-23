def _build_pnasnet_base(images,
                        normal_cell,
                        num_classes,
                        hparams,
                        is_training,
                        final_endpoint=None):
  """Constructs a PNASNet image model."""

  end_points = {}

  def add_and_check_endpoint(endpoint_name, net):
    end_points[endpoint_name] = net
    return final_endpoint and (endpoint_name == final_endpoint)

  # Find where to place the reduction cells or stride normal cells
  reduction_indices = nasnet_utils.calc_reduction_layers(
      hparams.num_cells, hparams.num_reduction_layers)

  # pylint: disable=protected-access
  stem = lambda: nasnet._imagenet_stem(images, hparams, normal_cell)
  # pylint: enable=protected-access
  net, cell_outputs = stem()
  if add_and_check_endpoint('Stem', net):
    return net, end_points

  # Setup for building in the auxiliary head.
  aux_head_cell_idxes = []
  if len(reduction_indices) >= 2:
    aux_head_cell_idxes.append(reduction_indices[1] - 1)

  # Run the cells
  filter_scaling = 1.0
  # true_cell_num accounts for the stem cells
  true_cell_num = 2
  activation_fn = tf.nn.relu6 if hparams.use_bounded_activation else tf.nn.relu
  for cell_num in range(hparams.num_cells):
    is_reduction = cell_num in reduction_indices
    stride = 2 if is_reduction else 1
    if is_reduction: filter_scaling *= hparams.filter_scaling_rate
    if hparams.skip_reduction_layer_input or not is_reduction:
      prev_layer = cell_outputs[-2]
    net = normal_cell(
        net,
        scope='cell_{}'.format(cell_num),
        filter_scaling=filter_scaling,
        stride=stride,
        prev_layer=prev_layer,
        cell_num=true_cell_num)
    if add_and_check_endpoint('Cell_{}'.format(cell_num), net):
      return net, end_points
    true_cell_num += 1
    cell_outputs.append(net)

    if (hparams.use_aux_head and cell_num in aux_head_cell_idxes and
        num_classes and is_training):
      aux_net = activation_fn(net)
      # pylint: disable=protected-access
      nasnet._build_aux_head(aux_net, end_points, num_classes, hparams,
                             scope='aux_{}'.format(cell_num))
      # pylint: enable=protected-access

  # Final softmax layer
  with tf.variable_scope('final_layer'):
    net = activation_fn(net)
    net = nasnet_utils.global_avg_pool(net)
    if add_and_check_endpoint('global_pool', net) or not num_classes:
      return net, end_points
    net = slim.dropout(net, hparams.dense_dropout_keep_prob, scope='dropout')
    logits = slim.fully_connected(net, num_classes)

    if add_and_check_endpoint('Logits', logits):
      return net, end_points

    predictions = tf.nn.softmax(logits, name='predictions')
    if add_and_check_endpoint('Predictions', predictions):
      return net, end_points
  return logits, end_points
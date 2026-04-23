def _s3d_cell(
      self,
      net: tf.Tensor,
      end_point: Text,
      end_points: Dict[Text, tf.Tensor],
      filters: Union[int, Sequence[Any]],
      non_local_block: Optional[tf_keras.layers.Layer] = None,
      attention_cell: Optional[tf_keras.layers.Layer] = None,
      attention_cell_super_graph: Optional[tf_keras.layers.Layer] = None
  ) -> Tuple[tf.Tensor, Dict[Text, tf.Tensor]]:
    if end_point.startswith('Mixed'):
      conv_type = (
          self._temporal_conv_type
          if end_point in self._temporal_conv_endpoints else '2d')
      use_self_gating_on_branch = (
          end_point in self._self_gating_endpoints and
          (self._gating_style == 'BRANCH' or
           self._gating_style == 'BRANCH_AND_CELL'))
      use_self_gating_on_cell = (
          end_point in self._self_gating_endpoints and
          (self._gating_style == 'CELL' or
           self._gating_style == 'BRANCH_AND_CELL'))
      net = self._get_inception_v1_cell_layer_impl()(
          branch_filters=net_utils.apply_depth_multiplier(
              filters, self._depth_multiplier),
          conv_type=conv_type,
          temporal_dilation_rate=1,
          swap_pool_and_1x1x1=self._swap_pool_and_1x1x1,
          use_self_gating_on_branch=use_self_gating_on_branch,
          use_self_gating_on_cell=use_self_gating_on_cell,
          use_sync_bn=self._use_sync_bn,
          norm_momentum=self._norm_momentum,
          norm_epsilon=self._norm_epsilon,
          kernel_initializer=self._kernel_initializer,
          temporal_conv_initializer=self._temporal_conv_initializer,
          kernel_regularizer=self._kernel_regularizer,
          parameterized_conv_layer=self._get_parameterized_conv_layer_impl(),
          name=self._get_layer_naming_fn()(end_point))(
              net)
    else:
      net = tf_keras.layers.MaxPool3D(
          pool_size=filters[0],
          strides=filters[1],
          padding='same',
          name=self._get_layer_naming_fn()(end_point))(
              net)
    end_points[end_point] = net
    if non_local_block:
      # TODO(b/182299420): Implement non local block in TF2.
      raise NotImplementedError('Non local block is not implemented yet.')
    if attention_cell:
      # TODO(b/182299420): Implement attention cell in TF2.
      raise NotImplementedError('Attention cell is not implemented yet.')
    if attention_cell_super_graph:
      # TODO(b/182299420): Implement attention cell super graph in TF2.
      raise NotImplementedError('Attention cell super graph is not implemented'
                                ' yet.')
    return net, end_points
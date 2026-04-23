def build(self, input_shape):
    if not isinstance(input_shape, list):
      raise ValueError('A BiFPN combine layer should be called '
                       'on a list of inputs.')
    if len(input_shape) < 2:
      raise ValueError('A BiFPN combine layer should be called '
                       'on a list of at least 2 inputs. '
                       'Got ' + str(len(input_shape)) + ' inputs.')
    if self.combine_method == 'sum':
      self._combine_op = tf.keras.layers.Add()
    elif self.combine_method == 'weighted_sum':
      self._combine_op = self._combine_weighted_sum
    elif self.combine_method == 'attention':
      self._combine_op = self._combine_attention
    elif self.combine_method == 'fast_attention':
      self._combine_op = self._combine_fast_attention
    else:
      raise ValueError('Unknown combine type: {}'.format(self.combine_method))
    if self.combine_method in {'weighted_sum', 'attention', 'fast_attention'}:
      self.per_input_weights = self.add_weight(
          name='bifpn_combine_weights',
          shape=(len(input_shape), 1),
          initializer='ones',
          trainable=True)
    super(BiFPNCombineLayer, self).build(input_shape)
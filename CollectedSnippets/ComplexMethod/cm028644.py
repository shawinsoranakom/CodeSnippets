def build(self, input_shape):
    dark_conv_args = {
        'activation': self._activation,
        'kernel_initializer': self._kernel_initializer,
        'bias_initializer': self._bias_initializer,
        'bias_regularizer': self._bias_regularizer,
        'use_sync_bn': self._use_sync_bn,
        'use_separable_conv': self._use_separable_conv,
        'norm_momentum': self._norm_momentum,
        'norm_epsilon': self._norm_epsilon,
        'kernel_regularizer': self._kernel_regularizer,
        'leaky_alpha': self._leaky_alpha,
    }

    csp = False
    self.layers = []
    for layer in self.layer_list:
      if layer == 'csp_route':
        self.layers.append(self._csp_route(self._filters, dark_conv_args))
        csp = True
      elif layer == 'csp_connect':
        self.layers.append(self._csp_connect(self._filters, dark_conv_args))
        csp = False
      elif layer == 'conv1':
        self.layers.append(self._conv1(self._filters, dark_conv_args, csp=csp))
      elif layer == 'conv2':
        self.layers.append(self._conv2(self._filters, dark_conv_args, csp=csp))
      elif layer == 'spp':
        self.layers.append(self._spp(self._filters, dark_conv_args))
      elif layer == 'sam':
        self.layers.append(self._sam(-1, dark_conv_args))

    self._lim = len(self.layers)
    super().build(input_shape)
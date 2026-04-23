def __init__(self,
               backbone,
               normalize_feature,
               hidden_dim,
               hidden_layer_num,
               hidden_norm_args,
               projection_dim,
               input_specs: Optional[Mapping[str,
                                             tf_keras.layers.InputSpec]] = None,
               dropout_rate: float = 0.0,
               aggregate_endpoints: bool = False,
               kernel_initializer='random_uniform',
               kernel_regularizer=None,
               bias_regularizer=None,
               **kwargs):
    """Video Classification initialization function.

    Args:
      backbone: a 3d backbone network.
      normalize_feature: whether normalize backbone feature.
      hidden_dim: `int` number of hidden units in MLP.
      hidden_layer_num: `int` number of hidden layers in MLP.
      hidden_norm_args: `dict` for batchnorm arguments in MLP.
      projection_dim: `int` number of output dimension for MLP.
      input_specs: `tf_keras.layers.InputSpec` specs of the input tensor.
      dropout_rate: `float` rate for dropout regularization.
      aggregate_endpoints: `bool` aggregate all end ponits or only use the
        final end point.
      kernel_initializer: kernel initializer for the dense layer.
      kernel_regularizer: tf_keras.regularizers.Regularizer object. Default to
        None.
      bias_regularizer: tf_keras.regularizers.Regularizer object. Default to
        None.
      **kwargs: keyword arguments to be passed.
    """
    if not input_specs:
      input_specs = {
          'image': layers.InputSpec(shape=[None, None, None, None, 3])
      }
    self._self_setattr_tracking = False
    self._config_dict = {
        'backbone': backbone,
        'normalize_feature': normalize_feature,
        'hidden_dim': hidden_dim,
        'hidden_layer_num': hidden_layer_num,
        'use_sync_bn': hidden_norm_args.use_sync_bn,
        'norm_momentum': hidden_norm_args.norm_momentum,
        'norm_epsilon': hidden_norm_args.norm_epsilon,
        'activation': hidden_norm_args.activation,
        'projection_dim': projection_dim,
        'input_specs': input_specs,
        'dropout_rate': dropout_rate,
        'aggregate_endpoints': aggregate_endpoints,
        'kernel_initializer': kernel_initializer,
        'kernel_regularizer': kernel_regularizer,
        'bias_regularizer': bias_regularizer,
    }
    self._input_specs = input_specs
    self._kernel_regularizer = kernel_regularizer
    self._bias_regularizer = bias_regularizer
    self._backbone = backbone

    inputs = {
        k: tf_keras.Input(shape=v.shape[1:]) for k, v in input_specs.items()
    }
    endpoints = backbone(inputs['image'])

    if aggregate_endpoints:
      pooled_feats = []
      for endpoint in endpoints.values():
        x_pool = tf_keras.layers.GlobalAveragePooling3D()(endpoint)
        pooled_feats.append(x_pool)
      x = tf.concat(pooled_feats, axis=1)
    else:
      x = endpoints[max(endpoints.keys())]
      x = tf_keras.layers.GlobalAveragePooling3D()(x)

    # L2 Normalize feature after backbone
    if normalize_feature:
      x = tf.nn.l2_normalize(x, axis=-1)

    # MLP hidden layers
    for _ in range(hidden_layer_num):
      x = tf_keras.layers.Dense(hidden_dim)(x)
      if self._config_dict['use_sync_bn']:
        x = tf_keras.layers.experimental.SyncBatchNormalization(
            momentum=self._config_dict['norm_momentum'],
            epsilon=self._config_dict['norm_epsilon'])(x)
      else:
        x = tf_keras.layers.BatchNormalization(
            momentum=self._config_dict['norm_momentum'],
            epsilon=self._config_dict['norm_epsilon'])(x)
      x = tf_utils.get_activation(self._config_dict['activation'])(x)

    # Projection head
    x = tf_keras.layers.Dense(projection_dim)(x)

    super().__init__(inputs=inputs, outputs=x, **kwargs)
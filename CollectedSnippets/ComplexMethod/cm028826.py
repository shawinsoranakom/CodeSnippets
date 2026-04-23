def __init__(
      self,
      min_level: int,
      max_level: int,
      num_classes: int,
      num_anchors_per_location: int | dict[str, int],
      num_convs: int = 4,
      num_filters: int = 256,
      attribute_heads: Optional[List[Dict[str, Any]]] = None,
      share_classification_heads: bool = False,
      use_separable_conv: bool = False,
      activation: str = 'relu',
      use_sync_bn: bool = False,
      norm_momentum: float = 0.99,
      norm_epsilon: float = 0.001,
      kernel_regularizer: Optional[tf_keras.regularizers.Regularizer] = None,
      bias_regularizer: Optional[tf_keras.regularizers.Regularizer] = None,
      num_params_per_anchor: int = 4,
      share_level_convs: bool = True,
      **kwargs,
  ):
    """Initializes a RetinaNet head.

    Args:
      min_level: An `int` number of minimum feature level.
      max_level: An `int` number of maximum feature level.
      num_classes: An `int` number of classes to predict.
      num_anchors_per_location: Number of anchors per pixel location. If an
        `int`, the same number is used for all levels. If a `dict`, it specifies
        the number at each level.
      num_convs: An `int` number that represents the number of the intermediate
        conv layers before the prediction.
      num_filters: An `int` number that represents the number of filters of the
        intermediate conv layers.
      attribute_heads: If not None, a list that contains a dict for each
        additional attribute head. Each dict consists of 4 key-value pairs:
        `name`, `type` ('regression' or 'classification'), `size` (number of
        predicted values for each instance), and `prediction_tower_name`
        (optional, specifies shared prediction towers.)
      share_classification_heads: A `bool` that indicates whether sharing
        weights among the main and attribute classification heads.
      use_separable_conv: A `bool` that indicates whether the separable
        convolution layers is used.
      activation: A `str` that indicates which activation is used, e.g. 'relu',
        'swish', etc.
      use_sync_bn: A `bool` that indicates whether to use synchronized batch
        normalization across different replicas.
      norm_momentum: A `float` of normalization momentum for the moving average.
      norm_epsilon: A `float` added to variance to avoid dividing by zero.
      kernel_regularizer: A `tf_keras.regularizers.Regularizer` object for
        Conv2D. Default is None.
      bias_regularizer: A `tf_keras.regularizers.Regularizer` object for Conv2D.
      num_params_per_anchor: Number of parameters required to specify an anchor
        box. For example, `num_params_per_anchor` would be 4 for axis-aligned
        anchor boxes specified by their y-centers, x-centers, heights, and
        widths.
      share_level_convs: An optional bool to enable sharing convs
        across levels for classnet, boxnet, classifier and box regressor.
        If True, convs will be shared across all levels.
      **kwargs: Additional keyword arguments to be passed.
    """
    super().__init__(**kwargs)
    self._config_dict = {
        'min_level': min_level,
        'max_level': max_level,
        'num_classes': num_classes,
        'num_anchors_per_location': num_anchors_per_location,
        'num_convs': num_convs,
        'num_filters': num_filters,
        'attribute_heads': attribute_heads,
        'share_classification_heads': share_classification_heads,
        'use_separable_conv': use_separable_conv,
        'activation': activation,
        'use_sync_bn': use_sync_bn,
        'norm_momentum': norm_momentum,
        'norm_epsilon': norm_epsilon,
        'kernel_regularizer': kernel_regularizer,
        'bias_regularizer': bias_regularizer,
        'num_params_per_anchor': num_params_per_anchor,
        'share_level_convs': share_level_convs,
    }

    if tf_keras.backend.image_data_format() == 'channels_last':
      self._bn_axis = -1
    else:
      self._bn_axis = 1
    self._activation = tf_utils.get_activation(activation)

    self._conv_kwargs = {
        'filters': self._config_dict['num_filters'],
        'kernel_size': 3,
        'padding': 'same',
        'bias_initializer': tf.zeros_initializer(),
        'bias_regularizer': self._config_dict['bias_regularizer'],
    }
    if not self._config_dict['use_separable_conv']:
      self._conv_kwargs.update({
          'kernel_initializer': tf_keras.initializers.RandomNormal(stddev=0.01),
          'kernel_regularizer': self._config_dict['kernel_regularizer'],
      })

    self._bn_kwargs = {
        'axis': self._bn_axis,
        'momentum': self._config_dict['norm_momentum'],
        'epsilon': self._config_dict['norm_epsilon'],
    }

    self._classifier_kwargs = {
        'kernel_size': 3,
        'padding': 'same',
        'bias_initializer': tf.constant_initializer(-np.log((1 - 0.01) / 0.01)),
        'bias_regularizer': self._config_dict['bias_regularizer'],
    }
    if isinstance(self._config_dict['num_anchors_per_location'], dict):
      self._classifier_kwargs['filters'] = {
          level: v * self._config_dict['num_classes']
          for level, v in self._config_dict['num_anchors_per_location'].items()
      }
    else:
      self._classifier_kwargs['filters'] = (
          self._config_dict['num_classes']
          * self._config_dict['num_anchors_per_location']
      )
    if self._config_dict['use_separable_conv']:
      self._classifier_kwargs.update({
          'depthwise_initializer': tf_keras.initializers.RandomNormal(
              stddev=0.03
          ),
          'depthwise_regularizer': self._config_dict['kernel_regularizer'],
          'pointwise_initializer': tf_keras.initializers.RandomNormal(
              stddev=0.03
          ),
          'pointwise_regularizer': self._config_dict['kernel_regularizer'],
      })
    else:
      self._classifier_kwargs.update({
          'kernel_initializer': tf_keras.initializers.RandomNormal(stddev=1e-5),
          'kernel_regularizer': self._config_dict['kernel_regularizer'],
      })

    self._box_regressor_kwargs = {
        'kernel_size': 3,
        'padding': 'same',
        'bias_initializer': tf.zeros_initializer(),
        'bias_regularizer': self._config_dict['bias_regularizer'],
    }
    if isinstance(self._config_dict['num_anchors_per_location'], dict):
      self._box_regressor_kwargs['filters'] = {
          level: v * self._config_dict['num_params_per_anchor']
          for level, v in self._config_dict['num_anchors_per_location'].items()
      }
    else:
      self._box_regressor_kwargs['filters'] = (
          self._config_dict['num_params_per_anchor']
          * self._config_dict['num_anchors_per_location']
      )
    if self._config_dict['use_separable_conv']:
      self._box_regressor_kwargs.update({
          'depthwise_initializer': tf_keras.initializers.RandomNormal(
              stddev=0.03
          ),
          'depthwise_regularizer': self._config_dict['kernel_regularizer'],
          'pointwise_initializer': tf_keras.initializers.RandomNormal(
              stddev=0.03
          ),
          'pointwise_regularizer': self._config_dict['kernel_regularizer'],
      })
    else:
      self._box_regressor_kwargs.update({
          'kernel_initializer': tf_keras.initializers.RandomNormal(stddev=1e-5),
          'kernel_regularizer': self._config_dict['kernel_regularizer'],
      })

    if self._config_dict['attribute_heads']:
      self._init_attribute_kwargs()
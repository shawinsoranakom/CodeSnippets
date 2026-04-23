def __init__(
      self,
      num_classes,
      num_convs=0,
      num_filters=256,
      use_separable_conv=False,
      num_fcs=2,
      fc_dims=1024,
      activation='relu',
      use_batch_norm=True,
      norm_activation=nn_ops.norm_activation_builder(activation='relu')):
    """Initialize params to build OLN box head.

    Args:
      num_classes: a integer for the number of classes.
      num_convs: `int` number that represents the number of the intermediate
        conv layers before the FC layers.
      num_filters: `int` number that represents the number of filters of the
        intermediate conv layers.
      use_separable_conv: `bool`, indicating whether the separable conv layers
        is used.
      num_fcs: `int` number that represents the number of FC layers before the
        predictions.
      fc_dims: `int` number that represents the number of dimension of the FC
        layers.
      activation: activation function. Support 'relu' and 'swish'.
      use_batch_norm: 'bool', indicating whether batchnorm layers are added.
      norm_activation: an operation that includes a normalization layer followed
        by an optional activation layer.
    """
    self._num_classes = num_classes

    self._num_convs = num_convs
    self._num_filters = num_filters
    if use_separable_conv:
      self._conv2d_op = functools.partial(
          tf_keras.layers.SeparableConv2D,
          depth_multiplier=1,
          bias_initializer=tf.zeros_initializer())
    else:
      self._conv2d_op = functools.partial(
          tf_keras.layers.Conv2D,
          kernel_initializer=tf_keras.initializers.VarianceScaling(
              scale=2, mode='fan_out', distribution='untruncated_normal'),
          bias_initializer=tf.zeros_initializer())

    self._num_fcs = num_fcs
    self._fc_dims = fc_dims
    if activation == 'relu':
      self._activation_op = tf.nn.relu
    elif activation == 'swish':
      self._activation_op = tf.nn.swish
    else:
      raise ValueError('Unsupported activation `{}`.'.format(activation))
    self._use_batch_norm = use_batch_norm
    self._norm_activation = norm_activation

    self._conv_ops = []
    self._conv_bn_ops = []
    for i in range(self._num_convs):
      self._conv_ops.append(
          self._conv2d_op(
              self._num_filters,
              kernel_size=(3, 3),
              strides=(1, 1),
              padding='same',
              dilation_rate=(1, 1),
              activation=(None
                          if self._use_batch_norm else self._activation_op),
              name='conv_{}'.format(i)))
      if self._use_batch_norm:
        self._conv_bn_ops.append(self._norm_activation())

    self._fc_ops = []
    self._fc_bn_ops = []
    for i in range(self._num_fcs):
      self._fc_ops.append(
          tf_keras.layers.Dense(
              units=self._fc_dims,
              activation=(None
                          if self._use_batch_norm else self._activation_op),
              name='fc{}'.format(i)))
      if self._use_batch_norm:
        self._fc_bn_ops.append(self._norm_activation(fused=False))

    self._class_predict = tf_keras.layers.Dense(
        self._num_classes,
        kernel_initializer=tf_keras.initializers.RandomNormal(stddev=0.01),
        bias_initializer=tf.zeros_initializer(),
        name='class-predict')
    self._box_predict = tf_keras.layers.Dense(
        self._num_classes * 4,
        kernel_initializer=tf_keras.initializers.RandomNormal(stddev=0.001),
        bias_initializer=tf.zeros_initializer(),
        name='box-predict')
    self._score_predict = tf_keras.layers.Dense(
        1,
        kernel_initializer=tf_keras.initializers.RandomNormal(stddev=0.01),
        bias_initializer=tf.zeros_initializer(),
        name='score-predict')
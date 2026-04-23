def __init__(self,
               filters=2,
               repetitions=2,
               insert_spp=False,
               insert_sam=False,
               insert_cbam=False,
               csp_stack=0,
               csp_scale=2,
               kernel_initializer='VarianceScaling',
               bias_initializer='zeros',
               bias_regularizer=None,
               kernel_regularizer=None,
               use_sync_bn=False,
               use_separable_conv=False,
               norm_momentum=0.99,
               norm_epsilon=0.001,
               block_invert=False,
               activation='leaky',
               leaky_alpha=0.1,
               spp_keys=None,
               **kwargs):
    """DarkRouteProcess initializer.

    Args:
      filters: the number of filters to be used in all subsequent layers
        filters should be the depth of the tensor input into this layer,
        as no downsampling can be done within this layer object.
      repetitions: number of times to repeat the processign nodes.
        for tiny: 1 repition, no spp allowed.
        for spp: insert_spp = True, and allow for 6 repetitions.
        for regular: insert_spp = False, and allow for 6 repetitions.
      insert_spp: bool if true add the spatial pyramid pooling layer.
      insert_sam: bool if true add spatial attention module to path.
      insert_cbam: bool if true add convolutional block attention
        module to path.
      csp_stack: int for the number of sequential layers from 0
        to <value> you would like to convert into a Cross Stage
        Partial(csp) type.
      csp_scale: int for how much to down scale the number of filters
        only for the csp layers in the csp section of the processing
        path. A value 2 indicates that each layer that is int eh CSP
        stack will have filters = filters/2.
      kernel_initializer: method to use to initialize kernel weights.
      bias_initializer: method to use to initialize the bias of the conv
        layers.
      bias_regularizer: string to indicate which function to use to regularizer
        bias.
      kernel_regularizer: string to indicate which function to use to
        regularizer weights.
      use_sync_bn: bool if true use the sync batch normalization.
      use_separable_conv: `bool` wether to use separable convs.
      norm_momentum: batch norm parameter see Tensorflow documentation.
      norm_epsilon: batch norm parameter see Tensorflow documentation.
      block_invert: bool use for switching between the even and odd
        repretions of layers. usually the repetition is based on a
        3x3 conv with filters, followed by a 1x1 with filters/2 with
        an even number of repetitions to ensure each 3x3 gets a 1x1
        sqeeze. block invert swaps the 3x3/1 1x1/2 to a 1x1/2 3x3/1
        ordering typically used when the model requires an odd number
        of repetiitions. All other peramters maintain their affects
      activation: activation function to use in processing.
      leaky_alpha: if leaky acitivation function, the alpha to use in
        processing the relu input.
      spp_keys: List[int] of the sampling levels to be applied by
        the Spatial Pyramid Pooling Layer. By default it is
        [5, 9, 13] inidicating a 5x5 pooling followed by 9x9
        followed by 13x13 then followed by the standard concatnation
        and convolution.
      **kwargs: Keyword Arguments.
    """

    super().__init__(**kwargs)
    # darkconv params
    self._filters = filters
    self._use_sync_bn = use_sync_bn
    self._use_separable_conv = use_separable_conv
    self._kernel_initializer = kernel_initializer
    self._bias_initializer = bias_initializer
    self._bias_regularizer = bias_regularizer
    self._kernel_regularizer = kernel_regularizer

    # normal params
    self._norm_momentum = norm_momentum
    self._norm_epsilon = norm_epsilon

    # activation params
    self._activation = activation
    self._leaky_alpha = leaky_alpha

    repetitions += (2 * int(insert_spp))
    if repetitions == 1:
      block_invert = True

    self._repetitions = repetitions
    self.layer_list, self.outputs = self._get_base_layers()

    if csp_stack > 0:
      self._csp_scale = csp_scale
      csp_stack += (2 * int(insert_spp))
      self._csp_filters = lambda x: x // csp_scale
      self._convert_csp(self.layer_list, self.outputs, csp_stack)
      block_invert = False

    self._csp_stack = csp_stack

    if block_invert:
      self._conv1_filters = lambda x: x
      self._conv2_filters = lambda x: x // 2
      self._conv1_kernel = (3, 3)
      self._conv2_kernel = (1, 1)
    else:
      self._conv1_filters = lambda x: x // 2
      self._conv2_filters = lambda x: x
      self._conv1_kernel = (1, 1)
      self._conv2_kernel = (3, 3)

    # insert SPP will always add to the total nuber of layer, never replace
    if insert_spp:
      self._spp_keys = spp_keys if spp_keys is not None else [5, 9, 13]
      self.layer_list = self._insert_spp(self.layer_list)

    if repetitions > 1:
      self.outputs[-2] = True

    if insert_sam:
      self.layer_list = self._insert_sam(self.layer_list, self.outputs)
      self._repetitions += 1
    self.outputs[-1] = True
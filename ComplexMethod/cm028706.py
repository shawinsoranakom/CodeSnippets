def __init__(self,
               feature_transform="exp",
               num_random_features=256,
               seed=0,
               redraw=False,
               is_short_seq=False,
               begin_kernel=0,
               scale=None,
               scale_by_length=False,
               use_causal_windowed=False,
               causal_chunk_length=1,
               causal_window_length=3,
               causal_window_decay=None,
               causal_padding=None,
               **kwargs):
    r"""Constructor of KernelAttention.

    Args:
      feature_transform: A non-linear transform of the keys and queries.
        Possible transforms are "elu", "relu", "square", "exp", "expplus",
        "expmod", "identity".
      num_random_features: Number of random features to be used for projection.
        if num_random_features <= 0, no production is used before transform.
      seed: The seed to begin drawing random features. Once the seed is set, the
        psedo number generation is determinisitc. Users should pass different
        seed for different layers. For multi-worker, each layer will use the
        same projection at each step.
      redraw: Whether to redraw projection every forward pass during training.
        The argument is only effective when num_random_features > 0.
      is_short_seq: boolean predicate indicating whether input data consists of
        very short sequences or not; in most cases this should be False (default
        option).
      begin_kernel: Apply kernel_attention after this sequence id and apply
        softmax attention before this.
      scale: The value to scale the dot product as described in `Attention Is
        All You Need`. If None, we use 1/sqrt(dk) as described in the paper.
      scale_by_length: boolean predicate indicating whether additionally scale
        the dot product based on key length. Set as log_512^(n) to stablize
        attention entropy against length. Refer to
        https://kexue.fm/archives/8823 for details.
      use_causal_windowed: If true perform windowed causal attention. See
        causal_windowed_performer_attention function docstring for more details.
      causal_chunk_length: Length of each chunk in tokens.
      causal_window_length: Length of attention window in chunks.
      causal_window_decay: Float window decay factor or `None`. If set,
        exponentially decay past attention window values by this factor before
        summation.
      causal_padding: Pad the query, value and key input tensors across the axis
        from either left or right if padding is set to "left" or "right"; apply
        no padding if padding is set to None. In the latter case, the axis
        dimension of the query, value and key input tensors must be divisible by
        the chunk_length.
      **kwargs: The same arguments `MultiHeadAttention` layer.
    """
    if feature_transform not in _TRANSFORM_MAP:
      raise ValueError("Unsupported feature_transform. The supported "
                       "feature_transform are %s. "
                       "Got '%s'." % (_TRANSFORM_MAP.keys(), feature_transform))
    if num_random_features <= 0 and redraw:
      raise ValueError(
          "There is nothing to redraw when num_random_features <= 0.")
    self._feature_transform = feature_transform
    self._num_random_features = num_random_features
    self._redraw = redraw
    self._is_short_seq = is_short_seq
    self._begin_kernel = begin_kernel
    self._scale_by_length = scale_by_length
    # We use the seed for two scenarios:
    # 1. inference
    # 2. no redraw
    self._seed = seed
    super().__init__(**kwargs)
    if scale is None:
      self._scale = 1.0 / math.sqrt(float(self._key_dim))
    else:
      self._scale = scale
    self._projection_matrix = None
    if num_random_features > 0:
      self._projection_matrix = create_projection_matrix(
          self._num_random_features, self._key_dim,
          tf.constant([self._seed, self._seed + 1]))
    self.use_causal_windowed = use_causal_windowed
    self.causal_chunk_length = causal_chunk_length
    self.causal_window_length = causal_window_length
    self.causal_window_decay = causal_window_decay
    self.causal_padding = causal_padding
    if self.use_causal_windowed and self._is_short_seq:
      raise ValueError(
          "use_causal_windowed and short_seq methods are mutually exclusive")
def __init__(
      self,
      variant: str = 'native',
      mlp_dim: int = 3072,
      num_heads: int = 12,
      num_layers: int = 12,
      attention_dropout_rate: float = 0.0,
      dropout_rate: float = 0.1,
      init_stochastic_depth_rate: float = 0.0,
      input_specs: layers.InputSpec = layers.InputSpec(
          shape=[None, None, None, None, 3]),
      temporal_patch_size: int = 4,
      spatial_patch_size: int = 16,
      hidden_size: int = 768,
      representation_size: int = 0,
      pooler: str = 'token',
      kernel_regularizer: Optional[tf_keras.regularizers.Regularizer] = None,
      original_init: bool = True,
      pos_embed_shape: Optional[
          Union[Tuple[int, int], Tuple[int, int, int]]] = None):
    """VisionTransformer initialization function.

    Args:
      variant: the implementation variant to use. Currently supporting
        ['native', 'mae'].
      mlp_dim: the mlp dimension in the transformer encoder.
      num_heads: number of heads in the transformer encoder.
      num_layers: number of layers in the transformer encoder.
      attention_dropout_rate: dropout probability within the attention layer.
      dropout_rate: the output layer dropout rate.
      init_stochastic_depth_rate: the initial stochastic depth rate.
      input_specs: the input shape.
      temporal_patch_size: the patch size for the temporal dimension.
      spatial_patch_size: the patch size for the spatial dimension.
      hidden_size: the projection hidden size for the first layer.
      representation_size: the feature size of representation.
      pooler: type of pooler to use. Accept 'none', 'token' or 'gap'.
      kernel_regularizer: kernel regularizer.
      original_init: whether to use the original init described in the paper.
      pos_embed_shape: the original positional embedding shape to use. If None,
        the positional embedding shape will be inferred from the inputs.
    """
    self._variant = variant
    self._mlp_dim = mlp_dim
    self._num_heads = num_heads
    self._num_layers = num_layers
    self._hidden_size = hidden_size
    self._representation_size = representation_size
    self._pooler = pooler
    self._input_specs = input_specs
    self._temporal_patch_size = temporal_patch_size
    self._spatial_patch_size = spatial_patch_size
    self._kernel_regularizer = kernel_regularizer
    self._original_init = original_init
    self._pos_embed_shape = pos_embed_shape

    self._patch_size = (
        self._temporal_patch_size,
        self._spatial_patch_size,
        self._spatial_patch_size,
    )
    nt = self._input_specs.shape[1] // self._temporal_patch_size
    nh = self._input_specs.shape[2] // self._spatial_patch_size
    nw = self._input_specs.shape[3] // self._spatial_patch_size

    inputs = tf_keras.Input(shape=input_specs.shape[1:])
    add_pos_embed = True
    if self._variant == 'native':
      x = self._tokenize(inputs)
    elif self._variant == 'mae':
      x = self._mae_tokenize(inputs)
      # NOTE: MAE variant adds pos_embed in the tokenizer.
      add_pos_embed = False
    else:
      raise ValueError(
          'Unrecognized ViT-3D implementation variant choice: %s' %
          variant)

    # If we want to add a class token, add it here.
    if pooler == 'token':
      x = TokenLayer(name='cls')(x)

    x = vit.Encoder(
        num_layers=num_layers,
        mlp_dim=mlp_dim,
        num_heads=num_heads,
        dropout_rate=dropout_rate,
        attention_dropout_rate=attention_dropout_rate,
        kernel_regularizer=kernel_regularizer,
        kernel_initializer='glorot_uniform' if original_init else dict(
            class_name='TruncatedNormal', config=dict(stddev=.02)),
        init_stochastic_depth_rate=init_stochastic_depth_rate,
        pos_embed_origin_shape=pos_embed_shape,
        pos_embed_target_shape=None,
        add_pos_embed=add_pos_embed)(x)

    if pooler == 'token':
      x = x[:, 0]
    elif pooler == 'gap':
      x = tf.reduce_mean(x, axis=1)
    elif pooler == 'none':
      x = tf.reshape(x, [-1, nt, nh, nw, x.shape[-1]], name='encoded_tokens')
    else:
      raise ValueError(f'unrecognized pooler type: {pooler}')

    if representation_size:
      x = tf_keras.layers.Dense(
          representation_size,
          kernel_regularizer=kernel_regularizer,
          name='pre_logits',
          kernel_initializer='lecun_normal' if original_init else 'he_uniform')(
              x)
      x = tf.nn.tanh(x)
    else:
      x = tf.identity(x, name='pre_logits')

    if pooler == 'none':
      endpoints = {'encoded_tokens': x}
    else:
      endpoints = {
          'pre_logits':
              tf.reshape(x, [-1, 1, 1, 1, representation_size or hidden_size])
      }

    super().__init__(inputs=inputs, outputs=endpoints)
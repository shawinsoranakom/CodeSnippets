def __init__(
      self,
      backbone: tf_keras.Model,
      num_classes: Union[List[int], int],
      input_specs: Optional[Mapping[str, tf_keras.layers.InputSpec]] = None,
      dropout_rate: float = 0.0,
      attention_num_heads: int = 6,
      attention_hidden_size: int = 768,
      attention_dropout_rate: float = 0.0,
      add_temporal_pos_emb_pooler: bool = False,
      aggregate_endpoints: bool = False,
      kernel_initializer: str = 'random_uniform',
      kernel_regularizer: Optional[tf_keras.regularizers.Regularizer] = None,
      bias_regularizer: Optional[tf_keras.regularizers.Regularizer] = None,
      require_endpoints: Optional[List[Text]] = None,
      classifier_type: str = 'linear',
      **kwargs):
    """Video Classification initialization function.

    Args:
      backbone: a 3d backbone network.
      num_classes: `int` number of classes in classification task.
      input_specs: `tf_keras.layers.InputSpec` specs of the input tensor.
      dropout_rate: `float` rate for dropout regularization.
      attention_num_heads: attention pooler layer number of heads.
      attention_hidden_size: attention pooler layer hidden size.
      attention_dropout_rate: attention map dropout regularization.
      add_temporal_pos_emb_pooler: `bool` adds a learnt temporal position
        embedding to the attention pooler.
      aggregate_endpoints: `bool` aggregate all end ponits or only use the
        final end point.
      kernel_initializer: kernel initializer for the dense layer.
      kernel_regularizer: tf_keras.regularizers.Regularizer object. Default to
        None.
      bias_regularizer: tf_keras.regularizers.Regularizer object. Default to
        None.
      require_endpoints: the required endpoints for prediction. If None or
        empty, then only uses the final endpoint.
      classifier_type: choose from 'linear' or 'pooler'.
      **kwargs: keyword arguments to be passed.
    """
    if not input_specs:
      input_specs = {
          'image': layers.InputSpec(shape=[None, None, None, None, 3])
      }
    self._self_setattr_tracking = False
    self._config_dict = {
        'backbone': backbone,
        'num_classes': num_classes,
        'input_specs': input_specs,
        'dropout_rate': dropout_rate,
        'attention_dropout_rate': attention_dropout_rate,
        'attention_num_heads': attention_num_heads,
        'attention_hidden_size': attention_hidden_size,
        'aggregate_endpoints': aggregate_endpoints,
        'kernel_initializer': kernel_initializer,
        'kernel_regularizer': kernel_regularizer,
        'bias_regularizer': bias_regularizer,
        'require_endpoints': require_endpoints,
    }
    self._input_specs = input_specs
    self._backbone = backbone

    inputs = {
        k: tf_keras.Input(shape=v.shape[1:]) for k, v in input_specs.items()
    }
    endpoints = backbone(inputs['image'])

    if classifier_type == 'linear':
      pool_or_flatten_op = tf_keras.layers.GlobalAveragePooling3D()
    elif classifier_type == 'pooler':
      pool_or_flatten_op = lambda x: tf.reshape(  # pylint:disable=g-long-lambda
          x,
          [
              tf.shape(x)[0],
              tf.shape(x)[1],
              tf.shape(x)[2] * tf.shape(x)[3],
              tf.shape(x)[4],
          ],
      )
    else:
      raise ValueError('%s classifier type not supported.' % classifier_type)

    if aggregate_endpoints:
      pooled_feats = []
      for endpoint in endpoints.values():
        x_pool = pool_or_flatten_op(endpoint)
        pooled_feats.append(x_pool)
      x = tf.concat(pooled_feats, axis=1)
    else:
      if not require_endpoints:
        # Use the last endpoint for prediction.
        x = endpoints[max(endpoints.keys())]
        x = pool_or_flatten_op(x)
      else:
        # Concat all the required endpoints for prediction.
        outputs = []
        for name in require_endpoints:
          x = endpoints[name]
          x = pool_or_flatten_op(x)
          outputs.append(x)
        x = tf.concat(outputs, axis=1)

    input_embeddings = tf.identity(x, name='embeddings')
    num_classes = [num_classes] if isinstance(num_classes, int) else num_classes
    outputs = []
    if classifier_type == 'linear':
      for nc in num_classes:
        x = tf_keras.layers.Dropout(dropout_rate)(input_embeddings)
        x = tf_keras.layers.Dense(
            nc, kernel_initializer=kernel_initializer,
            kernel_regularizer=kernel_regularizer,
            bias_regularizer=bias_regularizer)(x)
        outputs.append(x)
    elif classifier_type == 'pooler':
      for nc in num_classes:
        x = simple.AttentionPoolerClassificationHead(
            num_heads=attention_num_heads,
            hidden_size=attention_hidden_size,
            attention_dropout_rate=attention_dropout_rate,
            num_classes=nc,
            dropout_rate=dropout_rate,
            kernel_initializer=kernel_initializer,
            kernel_regularizer=kernel_regularizer,
            bias_regularizer=bias_regularizer,
            add_temporal_pos_embed=add_temporal_pos_emb_pooler)(
                input_embeddings)
        outputs.append(x)
    else:
      raise ValueError('%s classifier type not supported.')

    super().__init__(inputs=inputs, outputs=outputs, **kwargs)
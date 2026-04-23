def mobilenet_v2(input_shape=None,
                 alpha=1.0,
                 include_top=True,
                 classes=1000):
  """Instantiates the MobileNetV2 architecture.

  To load a MobileNetV2 model via `load_model`, import the custom
  objects `relu6` and pass them to the `custom_objects` parameter.
  E.g.
  model = load_model('mobilenet.h5', custom_objects={
                     'relu6': mobilenet.relu6})

  Args:
    input_shape: optional shape tuple, to be specified if you would
      like to use a model with an input img resolution that is not
      (224, 224, 3).
      It should have exactly 3 inputs channels (224, 224, 3).
      You can also omit this option if you would like
      to infer input_shape from an input_tensor.
      If you choose to include both input_tensor and input_shape then
      input_shape will be used if they match, if the shapes
      do not match then we will throw an error.
      E.g. `(160, 160, 3)` would be one valid value.
    alpha: controls the width of the network. This is known as the
    width multiplier in the MobileNetV2 paper.
      - If `alpha` < 1.0, proportionally decreases the number
          of filters in each layer.
      - If `alpha` > 1.0, proportionally increases the number
          of filters in each layer.
      - If `alpha` = 1, default number of filters from the paper
           are used at each layer.
    include_top: whether to include the fully-connected
      layer at the top of the network.
    classes: optional number of classes to classify images
      into, only to be specified if `include_top` is True, and
      if no `weights` argument is specified.

  Returns:
    A Keras model instance.

  Raises:
    ValueError: in case of invalid argument for `weights`,
        or invalid input shape or invalid depth_multiplier, alpha,
        rows when weights='imagenet'
  """

  # Determine proper input shape and default size.
  # If input_shape is None and no input_tensor
  if input_shape is None:
    default_size = 224

  # If input_shape is not None, assume default size
  else:
    if K.image_data_format() == 'channels_first':
      rows = input_shape[1]
      cols = input_shape[2]
    else:
      rows = input_shape[0]
      cols = input_shape[1]

    if rows == cols and rows in [96, 128, 160, 192, 224]:
      default_size = rows
    else:
      default_size = 224

  input_shape = _obtain_input_shape(input_shape,
                                    default_size=default_size,
                                    min_size=32,
                                    data_format=K.image_data_format(),
                                    require_flatten=include_top)

  if K.image_data_format() == 'channels_last':
    row_axis, col_axis = (0, 1)
  else:
    row_axis, col_axis = (1, 2)
  rows = input_shape[row_axis]
  cols = input_shape[col_axis]

  if K.image_data_format() != 'channels_last':
    warnings.warn('The MobileNet family of models is only available '
                  'for the input data format "channels_last" '
                  '(width, height, channels). '
                  'However your settings specify the default '
                  'data format "channels_first" (channels, width, height).'
                  ' You should set `image_data_format="channels_last"` '
                  'in your Keras config located at ~/.keras/keras.json. '
                  'The model being returned right now will expect inputs '
                  'to follow the "channels_last" data format.')
    K.set_image_data_format('channels_last')
    old_data_format = 'channels_first'
  else:
    old_data_format = None

  img_input = Input(shape=input_shape)

  first_block_filters = _make_divisible(32 * alpha, 8)
  x = Conv2D(first_block_filters,
             kernel_size=3,
             strides=(2, 2), padding='same',
             use_bias=False, name='Conv1')(img_input)
  x = BatchNormalization(epsilon=1e-3, momentum=0.999, name='bn_Conv1')(x)
  x = Activation(relu6, name='Conv1_relu')(x)

  x = _first_inverted_res_block(x,
                                filters=16,
                                alpha=alpha,
                                stride=1,
                                block_id=0)

  x = _inverted_res_block(x, filters=24, alpha=alpha, stride=2,
                          expansion=6, block_id=1)
  x = _inverted_res_block(x, filters=24, alpha=alpha, stride=1,
                          expansion=6, block_id=2)

  x = _inverted_res_block(x, filters=32, alpha=alpha, stride=2,
                          expansion=6, block_id=3)
  x = _inverted_res_block(x, filters=32, alpha=alpha, stride=1,
                          expansion=6, block_id=4)
  x = _inverted_res_block(x, filters=32, alpha=alpha, stride=1,
                          expansion=6, block_id=5)

  x = _inverted_res_block(x, filters=64, alpha=alpha, stride=2,
                          expansion=6, block_id=6)
  x = _inverted_res_block(x, filters=64, alpha=alpha, stride=1,
                          expansion=6, block_id=7)
  x = _inverted_res_block(x, filters=64, alpha=alpha, stride=1,
                          expansion=6, block_id=8)
  x = _inverted_res_block(x, filters=64, alpha=alpha, stride=1,
                          expansion=6, block_id=9)

  x = _inverted_res_block(x, filters=96, alpha=alpha, stride=1,
                          expansion=6, block_id=10)
  x = _inverted_res_block(x, filters=96, alpha=alpha, stride=1,
                          expansion=6, block_id=11)
  x = _inverted_res_block(x, filters=96, alpha=alpha, stride=1,
                          expansion=6, block_id=12)

  x = _inverted_res_block(x, filters=160, alpha=alpha, stride=2,
                          expansion=6, block_id=13)
  x = _inverted_res_block(x, filters=160, alpha=alpha, stride=1,
                          expansion=6, block_id=14)
  x = _inverted_res_block(x, filters=160, alpha=alpha, stride=1,
                          expansion=6, block_id=15)

  x = _inverted_res_block(x, filters=320, alpha=alpha, stride=1,
                          expansion=6, block_id=16)

  # no alpha applied to last conv as stated in the paper:
  # if the width multiplier is greater than 1 we
  # increase the number of output channels
  if alpha > 1.0:
    last_block_filters = _make_divisible(1280 * alpha, 8)
  else:
    last_block_filters = 1280

  x = Conv2D(last_block_filters,
             kernel_size=1,
             use_bias=False,
             name='Conv_1')(x)
  x = BatchNormalization(epsilon=1e-3, momentum=0.999, name='Conv_1_bn')(x)
  x = Activation(relu6, name='out_relu')(x)

  if include_top:
    x = GlobalAveragePooling2D()(x)
    x = Dense(classes, activation='softmax',
              use_bias=True, name='Logits')(x)

  # Ensure that the model takes into account
  # any potential predecessors of `input_tensor`.
  inputs = img_input

  # Create model.
  model = Model(inputs, x, name='mobilenetv2_%0.2f_%s' % (alpha, rows))

  if old_data_format:
    K.set_image_data_format(old_data_format)
  return model
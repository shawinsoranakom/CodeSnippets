def resnet_v1_beta(inputs,
                   blocks,
                   num_classes=None,
                   is_training=None,
                   global_pool=True,
                   output_stride=None,
                   root_block_fn=None,
                   reuse=None,
                   scope=None,
                   sync_batch_norm_method='None'):
  """Generator for v1 ResNet models (beta variant).

  This function generates a family of modified ResNet v1 models. In particular,
  the first original 7x7 convolution is replaced with three 3x3 convolutions.
  See the resnet_v1_*() methods for specific model instantiations, obtained by
  selecting different block instantiations that produce ResNets of various
  depths.

  The code is modified from slim/nets/resnet_v1.py, and please refer to it for
  more details.

  Args:
    inputs: A tensor of size [batch, height_in, width_in, channels].
    blocks: A list of length equal to the number of ResNet blocks. Each element
      is a resnet_utils.Block object describing the units in the block.
    num_classes: Number of predicted classes for classification tasks. If None
      we return the features before the logit layer.
    is_training: Enable/disable is_training for batch normalization.
    global_pool: If True, we perform global average pooling before computing the
      logits. Set to True for image classification, False for dense prediction.
    output_stride: If None, then the output will be computed at the nominal
      network stride. If output_stride is not None, it specifies the requested
      ratio of input to output spatial resolution.
    root_block_fn: The function consisting of convolution operations applied to
      the root input. If root_block_fn is None, use the original setting of
      RseNet-v1, which is simply one convolution with 7x7 kernel and stride=2.
    reuse: whether or not the network and its variables should be reused. To be
      able to reuse 'scope' must be given.
    scope: Optional variable_scope.
    sync_batch_norm_method: String, sync batchnorm method.

  Returns:
    net: A rank-4 tensor of size [batch, height_out, width_out, channels_out].
      If global_pool is False, then height_out and width_out are reduced by a
      factor of output_stride compared to the respective height_in and width_in,
      else both height_out and width_out equal one. If num_classes is None, then
      net is the output of the last ResNet block, potentially after global
      average pooling. If num_classes is not None, net contains the pre-softmax
      activations.
    end_points: A dictionary from components of the network to the corresponding
      activation.

  Raises:
    ValueError: If the target output_stride is not valid.
  """
  if root_block_fn is None:
    root_block_fn = functools.partial(conv2d_ws.conv2d_same,
                                      num_outputs=64,
                                      kernel_size=7,
                                      stride=2,
                                      scope='conv1')
  batch_norm = utils.get_batch_norm_fn(sync_batch_norm_method)
  with tf.variable_scope(scope, 'resnet_v1', [inputs], reuse=reuse) as sc:
    end_points_collection = sc.original_name_scope + '_end_points'
    with slim.arg_scope([
        conv2d_ws.conv2d, bottleneck, lite_bottleneck,
        resnet_utils.stack_blocks_dense
    ],
                        outputs_collections=end_points_collection):
      if is_training is not None:
        arg_scope = slim.arg_scope([batch_norm], is_training=is_training)
      else:
        arg_scope = slim.arg_scope([])
      with arg_scope:
        net = inputs
        if output_stride is not None:
          if output_stride % 4 != 0:
            raise ValueError('The output_stride needs to be a multiple of 4.')
          output_stride //= 4
        net = root_block_fn(net)
        net = slim.max_pool2d(net, 3, stride=2, padding='SAME', scope='pool1')
        net = resnet_utils.stack_blocks_dense(net, blocks, output_stride)

        if global_pool:
          # Global average pooling.
          net = tf.reduce_mean(net, [1, 2], name='pool5', keepdims=True)
        if num_classes is not None:
          net = conv2d_ws.conv2d(net, num_classes, [1, 1], activation_fn=None,
                                 normalizer_fn=None, scope='logits',
                                 use_weight_standardization=False)
        # Convert end_points_collection into a dictionary of end_points.
        end_points = slim.utils.convert_collection_to_dict(
            end_points_collection)
        if num_classes is not None:
          end_points['predictions'] = slim.softmax(net, scope='predictions')
        return net, end_points
def stack_blocks_dense(net, blocks, output_stride=None,
                       store_non_strided_activations=False,
                       outputs_collections=None):
  """Stacks ResNet `Blocks` and controls output feature density.

  First, this function creates scopes for the ResNet in the form of
  'block_name/unit_1', 'block_name/unit_2', etc.

  Second, this function allows the user to explicitly control the ResNet
  output_stride, which is the ratio of the input to output spatial resolution.
  This is useful for dense prediction tasks such as semantic segmentation or
  object detection.

  Most ResNets consist of 4 ResNet blocks and subsample the activations by a
  factor of 2 when transitioning between consecutive ResNet blocks. This results
  to a nominal ResNet output_stride equal to 8. If we set the output_stride to
  half the nominal network stride (e.g., output_stride=4), then we compute
  responses twice.

  Control of the output feature density is implemented by atrous convolution.

  Args:
    net: A `Tensor` of size [batch, height, width, channels].
    blocks: A list of length equal to the number of ResNet `Blocks`. Each
      element is a ResNet `Block` object describing the units in the `Block`.
    output_stride: If `None`, then the output will be computed at the nominal
      network stride. If output_stride is not `None`, it specifies the requested
      ratio of input to output spatial resolution, which needs to be equal to
      the product of unit strides from the start up to some level of the ResNet.
      For example, if the ResNet employs units with strides 1, 2, 1, 3, 4, 1,
      then valid values for the output_stride are 1, 2, 6, 24 or None (which
      is equivalent to output_stride=24).
    store_non_strided_activations: If True, we compute non-strided (undecimated)
      activations at the last unit of each block and store them in the
      `outputs_collections` before subsampling them. This gives us access to
      higher resolution intermediate activations which are useful in some
      dense prediction problems but increases 4x the computation and memory cost
      at the last unit of each block.
    outputs_collections: Collection to add the ResNet block outputs.

  Returns:
    net: Output tensor with stride equal to the specified output_stride.

  Raises:
    ValueError: If the target output_stride is not valid.
  """
  # The current_stride variable keeps track of the effective stride of the
  # activations. This allows us to invoke atrous convolution whenever applying
  # the next residual unit would result in the activations having stride larger
  # than the target output_stride.
  current_stride = 1

  # The atrous convolution rate parameter.
  rate = 1

  for block in blocks:
    with tf.variable_scope(block.scope, 'block', [net]) as sc:
      block_stride = 1
      for i, unit in enumerate(block.args):
        if store_non_strided_activations and i == len(block.args) - 1:
          # Move stride from the block's last unit to the end of the block.
          block_stride = unit.get('stride', 1)
          unit = dict(unit, stride=1)

        with tf.variable_scope('unit_%d' % (i + 1), values=[net]):
          # If we have reached the target output_stride, then we need to employ
          # atrous convolution with stride=1 and multiply the atrous rate by the
          # current unit's stride for use in subsequent layers.
          if output_stride is not None and current_stride == output_stride:
            net = block.unit_fn(net, rate=rate, **dict(unit, stride=1))
            rate *= unit.get('stride', 1)

          else:
            net = block.unit_fn(net, rate=1, **unit)
            current_stride *= unit.get('stride', 1)
            if output_stride is not None and current_stride > output_stride:
              raise ValueError('The target output_stride cannot be reached.')

      # Collect activations at the block's end before performing subsampling.
      net = slim.utils.collect_named_outputs(outputs_collections, sc.name, net)

      # Subsampling of the block's output activations.
      if output_stride is not None and current_stride == output_stride:
        rate *= block_stride
      else:
        net = subsample(net, block_stride)
        current_stride *= block_stride
        if output_stride is not None and current_stride > output_stride:
          raise ValueError('The target output_stride cannot be reached.')

  if output_stride is not None and current_stride != output_stride:
    raise ValueError('The target output_stride cannot be reached.')

  return net
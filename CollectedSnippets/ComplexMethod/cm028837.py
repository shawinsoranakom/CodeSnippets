def block_spec_decoder(
    specs: dict[Any, Any],
    filter_size_scale: float,
    # Set to 1 for mobilenetv1.
    divisible_by: int = 8,
    finegrain_classification_mode: bool = True,
):
  """Decodes specs for a block.

  Args:
    specs: A `dict` specification of block specs of a mobilenet version.
    filter_size_scale: A `float` multiplier for the filter size for all
      convolution ops. The value must be greater than zero. Typical usage will
      be to set this value in (0, 1) to reduce the number of parameters or
      computation cost of the model.
    divisible_by: An `int` that ensures all inner dimensions are divisible by
      this number.
    finegrain_classification_mode: If True, the model will keep the last layer
      large even for small multipliers, following
      https://arxiv.org/abs/1801.04381.

  Returns:
    A list of `BlockSpec` that defines structure of the base network.
  """

  spec_name = specs['spec_name']
  block_spec_schema = specs['block_spec_schema']
  block_specs = specs['block_specs']

  if not block_specs:
    raise ValueError(
        'The block spec cannot be empty for {} !'.format(spec_name))

  for block_spec in block_specs:
    if len(block_spec) != len(block_spec_schema):
      raise ValueError(
          'The block spec values {} do not match with the schema {}'.format(
              block_spec, block_spec_schema
          )
      )

  decoded_specs = []

  for s in block_specs:
    kw_s = dict(zip(block_spec_schema, s))
    decoded_specs.append(BlockSpec(**kw_s))

  # This adjustment applies to V2, V3, and V4
  if (spec_name != 'MobileNetV1'
      and finegrain_classification_mode
      and filter_size_scale < 1.0):
    decoded_specs[-1].filters /= filter_size_scale  # pytype: disable=annotation-type-mismatch

  for ds in decoded_specs:
    if ds.filters:
      ds.filters = nn_layers.round_filters(filters=ds.filters,
                                           multiplier=filter_size_scale,
                                           divisor=divisible_by,
                                           min_depth=8)

  return decoded_specs
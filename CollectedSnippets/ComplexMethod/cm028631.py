def mobilenet_edgetpu_v2_base(
    width_coefficient: float = 1.0,
    depth_coefficient: float = 1.0,
    stem_base_filters: int = 64,
    stem_kernel_size: int = 5,
    top_base_filters: int = 1280,
    group_base_size: int = 64,
    dropout_rate: float = 0.2,
    drop_connect_rate: float = 0.1,
    filter_size_overrides: Optional[Dict[int, int]] = None,
    block_op_overrides: Optional[Dict[int, Dict[int, Dict[str, Any]]]] = None,
    block_group_overrides: Optional[Dict[int, Dict[str, Any]]] = None,
    topology: Optional[TopologyConfig] = None):
  """Creates MobilenetEdgeTPUV2 ModelConfig based on tuning parameters."""

  config = ModelConfig()
  param_overrides = {
      'width_coefficient': width_coefficient,
      'depth_coefficient': depth_coefficient,
      'stem_base_filters': stem_base_filters,
      'stem_kernel_size': stem_kernel_size,
      'top_base_filters': top_base_filters,
      'group_base_size': group_base_size,
      'dropout_rate': dropout_rate,
      'drop_connect_rate': drop_connect_rate
  }
  config = config.replace(**param_overrides)

  topology_config = TopologyConfig() if topology is None else topology
  if filter_size_overrides:
    for group_id in filter_size_overrides:
      topology_config.block_groups[group_id].filters = filter_size_overrides[
          group_id]

  if block_op_overrides:
    for group_id in block_op_overrides:
      for block_id in block_op_overrides[group_id]:
        replaced_block = topology_config.block_groups[group_id].blocks[
            block_id].replace(**block_op_overrides[group_id][block_id])
        topology_config.block_groups[group_id].blocks[block_id] = replaced_block

  if block_group_overrides:
    for group_id in block_group_overrides:
      replaced_group = topology_config.block_groups[group_id].replace(
          **block_group_overrides[group_id])
      topology_config.block_groups[group_id] = replaced_group

  blocks = ()
  input_filters = stem_base_filters

  for group in topology_config.block_groups:
    for block_search in group.blocks:
      if block_search.op_type != BlockType.skip:
        block = BlockConfig.from_search_config(
            input_filters=input_filters,
            output_filters=group.filters,
            block_search_config=block_search)
        blocks += (block,)
        # Set input filters for the next block
        input_filters = group.filters

  config = config.replace(blocks=blocks)

  return config
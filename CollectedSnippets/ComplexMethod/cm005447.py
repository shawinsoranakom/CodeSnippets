def load(module: nn.Module, state_dict, prefix="", assign_to_params_buffers=False):
        local_metadata = {} if metadata is None else metadata.get(prefix[:-1], {})
        local_metadata["assign_to_params_buffers"] = assign_to_params_buffers

        args = (state_dict, prefix, local_metadata, True, [], [], error_msgs)
        # Parameters of module and children will start with prefix. We can exit early if there are none in this
        # state_dict
        if is_deepspeed_zero3_enabled():
            import deepspeed

            # In sharded models, each shard has only part of the full state_dict, so only gather
            # parameters that are in the current state_dict.
            named_parameters = dict(module.named_parameters(prefix=prefix[:-1], recurse=False))
            params_to_gather = []
            for k in named_parameters:
                if k in state_dict:
                    param = named_parameters[k]
                    # crucial to not init the weight again
                    param._is_hf_initialized = True
                    params_to_gather.append(param)
                    missing_keys.discard(k)

            if len(params_to_gather) > 0:
                # because zero3 puts placeholders in model params, this context
                # manager gathers (unpartitions) the params of the current layer, then loads from
                # the state dict and then re-partitions them again
                with deepspeed.zero.GatheredParameters(params_to_gather, modifier_rank=0):
                    if torch.distributed.get_rank() == 0:
                        module._load_from_state_dict(*args)

            # Buffers are not partitioned by ZeRO-3, load them directly
            named_buffers = dict(module.named_buffers(prefix=prefix[:-1], recurse=False))
            for k, buf in named_buffers.items():
                if k in state_dict and buf is not None:
                    missing_keys.discard(k)
                    with torch.no_grad():
                        buf.copy_(state_dict[k])
                    buf._is_hf_initialized = True

        for name, child in module._modules.items():
            if child is not None:
                load(child, state_dict, prefix + name + ".", assign_to_params_buffers)
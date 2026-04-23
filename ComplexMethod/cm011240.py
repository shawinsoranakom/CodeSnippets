def shard_module(module: nn.Module, plan: ShardingPlan, src_rank=0, process_group=None):
    """
    Shards a given module according to the provided sharding `plan`. This method
    first shards all the parameters according to the given sharding `plan`. Then if
    `output_plan` and `return_local_tensor` are specified in the sharding `plan`, it
    will tag the output of modules according `output_plan`, convert the module's
    output back to data parallel according to `return_local_tensor`.

    Needs to be called on all ranks in an SPMD fashion.

    Args:
        module (:class:`torch.nn.Module`): The module to apply sharding to
        plan (:class:`torch.distributed._shard.sharding_plan.ShardingPlan`):
            The ShardingPlan which specified param name to ShardingSpec to apply to
            each parameter.

    Keyword args:
         src_rank (int, optional): The source rank which is used as the ground truth of
            the data for the module that would be sharded and scattered across the rest
            of the ranks.
            Default: 0.
        process_group (ProcessGroup, optional): The process group to work on. If None,
            the default process group will be used.
    """
    # record Sharder paths for sanity check on the plan to ensure items in the plan
    # does not conflict with the submodule tree that the Sharder is working with
    sharder_paths = []
    for name, spec in plan.plan.items():
        if isinstance(spec, Sharder):
            sharder_paths.append(name)

    # shard the parameter according to the ShardingPlan
    for name, spec in plan.plan.items():
        if isinstance(spec, ShardingSpec):
            # if found a sharding spec, try to shard the parameter
            module_path, _, param_name = name.rpartition(".")

            for sharder_path in sharder_paths:
                if module_path.startswith(sharder_path):
                    raise RuntimeError(
                        f"ShardingPlan is in-valid, trying to shard a parameter: {name},"
                        f" but there's already a Sharder entry for module {sharder_path},"
                        f" parameter sharding should not conflict with the submodule tree"
                        f" that a Sharder is working with!"
                    )

            mod = module.get_submodule(module_path)
            shard_parameter(
                mod, param_name, spec, src_rank=src_rank, process_group=process_group
            )
        elif isinstance(spec, Sharder):
            parent_mod_path, _, _mod_name = name.rpartition(".")
            if name == "":
                raise KeyError("Module path must not be empty for custom sharder!")
            mod = module.get_submodule(name)
            parent_mod = module.get_submodule(parent_mod_path)
            sharded_mod = spec.shard(mod)
            # swap this submodule with the sharded module
            parent_mod.mod_name = sharded_mod
        else:
            raise TypeError(
                f"Only `ShardingSpec` and `Sharder` are supported to shard '{name}'"
            )

    # reshard output if there's an entry in `reshard_output` for this module
    if plan.output_plan is not None:
        for module_path, output_spec in plan.output_plan.items():
            if isinstance(output_spec, ShardingSpec):
                mod = module.get_submodule(module_path)
                _reshard_output(mod, output_spec)
            else:
                raise TypeError(
                    f"Only `ShardingSpec` is supported as output_plan for '{module_path}'"
                )
    # convert the output back to data parallel for the modules appears in
    # `return_local_tensor` of the plan, we will call `_collect_local_shard`
    # to collect the local tensor for output of modules
    if plan.return_local_tensor is not None:
        for module_path in plan.return_local_tensor:
            mod = module.get_submodule(module_path)
            _collect_local_shard(mod)
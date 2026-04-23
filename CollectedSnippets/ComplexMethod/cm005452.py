def wrap_model_xla_fsdp(model, args, is_fsdp_xla_v2_enabled):
    """
    Wraps a model with XLA Fully Sharded Data Parallelism (FSDP).

    Handles both FSDP v1 (`XlaFullyShardedDataParallel`) and v2 (`SpmdFullyShardedDataParallel`),
    including auto-wrap policies, gradient checkpointing, and patching `xm.optimizer_step`.

    Args:
        model (`torch.nn.Module`): The model to wrap.
        args (`TrainingArguments`): The training arguments containing FSDP configuration.
        is_fsdp_xla_v2_enabled (`bool`): Whether FSDP v2 (SPMD) is enabled.

    Returns:
        `torch.nn.Module`: The FSDP-wrapped model.
    """
    import torch_xla.core.xla_model as xm
    import torch_xla.distributed.spmd as xs

    from ..trainer_pt_utils import get_module_class_from_name

    try:
        from torch_xla.distributed.fsdp import XlaFullyShardedDataParallel as FSDP
        from torch_xla.distributed.fsdp import checkpoint_module
        from torch_xla.distributed.fsdp.wrap import (
            size_based_auto_wrap_policy,
            transformer_auto_wrap_policy,
        )

        if is_fsdp_xla_v2_enabled:
            from torch_xla.experimental.spmd_fully_sharded_data_parallel import (
                SpmdFullyShardedDataParallel as FSDPv2,
            )
    except ImportError:
        raise ImportError("Missing XLA FSDP related module; please make sure to use torch-xla >= 2.0.")

    auto_wrap_policy = None
    auto_wrapper_callable = None
    default_transformer_cls_names_to_wrap = getattr(model, "_no_split_modules", None)
    fsdp_transformer_layer_cls_to_wrap = args.fsdp_config.get(
        "transformer_layer_cls_to_wrap", default_transformer_cls_names_to_wrap
    )

    if args.fsdp_config["min_num_params"] > 0:
        auto_wrap_policy = functools.partial(
            size_based_auto_wrap_policy, min_num_params=args.fsdp_config["min_num_params"]
        )
    elif fsdp_transformer_layer_cls_to_wrap is not None:
        transformer_cls_to_wrap = set()
        for layer_class in fsdp_transformer_layer_cls_to_wrap:
            transformer_cls = get_module_class_from_name(model, layer_class)
            if transformer_cls is None:
                raise Exception("Could not find the transformer layer class to wrap in the model.")
            else:
                transformer_cls_to_wrap.add(transformer_cls)

        auto_wrap_policy = functools.partial(
            transformer_auto_wrap_policy,
            # Transformer layer class to wrap
            transformer_layer_cls=transformer_cls_to_wrap,
        )

    fsdp_kwargs = args.xla_fsdp_config
    if args.fsdp_config["xla_fsdp_grad_ckpt"]:
        if model.config.use_cache:
            logger.warning_once(
                "`use_cache=True` is incompatible with gradient checkpointing. Setting `use_cache=False`."
            )
            model.config.use_cache = False

        # Apply gradient checkpointing to auto-wrapped sub-modules if specified
        def auto_wrapper_callable(m, *args, **kwargs):
            target_cls = FSDP if not is_fsdp_xla_v2_enabled else FSDPv2
            return target_cls(checkpoint_module(m), *args, **kwargs)

    # Wrap the base model with an outer FSDP wrapper
    if is_fsdp_xla_v2_enabled:

        def shard_output(output, mesh):
            from ..modeling_outputs import CausalLMOutputWithPast

            real_output = None
            if isinstance(output, torch.Tensor):
                real_output = output
            elif isinstance(output, tuple):
                real_output = output[0]
            elif isinstance(output, CausalLMOutputWithPast):
                real_output = output.logits

            if real_output is None:
                raise ValueError("Something went wrong, the output of the model shouldn't be `None`")
            xs.mark_sharding(real_output, mesh, ("fsdp", None, None))

        model = FSDPv2(
            model,
            shard_output=shard_output,
            auto_wrap_policy=auto_wrap_policy,
            auto_wrapper_callable=auto_wrapper_callable,
        )
    else:
        model = FSDP(
            model,
            auto_wrap_policy=auto_wrap_policy,
            auto_wrapper_callable=auto_wrapper_callable,
            **fsdp_kwargs,
        )

    # Patch `xm.optimizer_step` should not reduce gradients in this case,
    # as FSDP does not need gradient reduction over sharded parameters.
    def patched_optimizer_step(optimizer, barrier=False, optimizer_args={}):
        loss = optimizer.step(**optimizer_args)
        if barrier:
            xm.mark_step()
        return loss

    xm.optimizer_step = patched_optimizer_step

    return model
def _get_bitsandbytes_optimizer(ctx: OptimizerContext) -> tuple[Any, dict[str, Any]]:
    """Get bitsandbytes optimizer (AdamW, Lion, RMSprop variants)."""
    if not is_bitsandbytes_available():
        raise ImportError(
            "You need to install `bitsandbytes` in order to use bitsandbytes optimizers: `pip install -U bitsandbytes`"
        )

    from bitsandbytes.optim import AdamW, Lion, RMSprop

    optim_name = ctx.args.optim
    is_paged = "paged" in optim_name
    optim_bits = 8 if "8bit" in optim_name else 32
    optimizer_cls = None
    additional_optim_kwargs = ctx.adam_kwargs

    if "adam" in optim_name:
        optimizer_cls = AdamW
    elif "lion" in optim_name:
        optimizer_cls = Lion
        additional_optim_kwargs = {"betas": (ctx.args.adam_beta1, ctx.args.adam_beta2)}
    elif "rmsprop" in optim_name:
        optimizer_cls = RMSprop
        additional_optim_kwargs = ctx.optim_args
    elif "ademamix" in optim_name:
        from bitsandbytes.optim import AdEMAMix

        optimizer_cls = AdEMAMix
        additional_optim_kwargs = {
            "betas": (
                float(ctx.optim_args.get("beta1", ctx.args.adam_beta1)),
                float(ctx.optim_args.get("beta2", ctx.args.adam_beta2)),
                float(ctx.optim_args.get("beta3", 0.9999)),
            ),
            "alpha": float(ctx.optim_args.get("alpha", 5.0)),
            "eps": float(ctx.optim_args.get("eps", ctx.args.adam_epsilon)),
        }
        if "t_alpha" in ctx.optim_args:
            additional_optim_kwargs["t_alpha"] = int(ctx.optim_args["t_alpha"])
        if "t_beta3" in ctx.optim_args:
            additional_optim_kwargs["t_beta3"] = int(ctx.optim_args["t_beta3"])

    bnb_kwargs = {"optim_bits": optim_bits}
    if "rmsprop" not in optim_name:
        bnb_kwargs["is_paged"] = is_paged

    ctx.optimizer_kwargs.update(additional_optim_kwargs)
    ctx.optimizer_kwargs.update(bnb_kwargs)
    return optimizer_cls, ctx.optimizer_kwargs
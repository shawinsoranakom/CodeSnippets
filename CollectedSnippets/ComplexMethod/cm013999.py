def patch() -> None:
        # A better way to disable the following would be decorate the source
        # functions with @torch._disable_dynamo. However, this causes issues
        # with torch.deploy internally.
        from .decorators import disable

        torch.jit.trace = disable(
            torch.jit.trace, reason="tracing into TorchScript not fully supported"
        )
        torch.jit.trace_module = disable(
            torch.jit.trace_module,
            reason="tracing into TorchScript not fully supported",
        )
        torch.jit._get_trace_graph = disable(
            torch.jit._get_trace_graph,
            reason="tracing into TorchScript not fully supported",
        )
        torch.fx._symbolic_trace.Tracer.trace = disable(
            torch.fx._symbolic_trace.Tracer.trace,
            reason="tracing into FX not fully supported",
        )
        torch.distributions.Distribution.set_default_validate_args(False)

        from torch.optim import (
            adadelta,
            adagrad,
            adam,
            adamax,
            adamw,
            asgd,
            lbfgs,
            nadam,
            radam,
            rmsprop,
            rprop,
            sgd,
            sparse_adam,
        )

        optimizer_modules = {
            adadelta,
            adagrad,
            adam,
            adamax,
            adamw,
            asgd,
            lbfgs,
            nadam,
            radam,
            rmsprop,
            rprop,
            sgd,
            sparse_adam,
        }

        for opt_mod in optimizer_modules:
            opt_name = opt_mod.__name__.split(".")[-1]
            fused_fn_name = f"_fused_{opt_name}"

            if hasattr(opt_mod, fused_fn_name):
                setattr(
                    opt_mod,
                    fused_fn_name,
                    disable(
                        getattr(opt_mod, fused_fn_name),
                        reason="don't trace into fused optimizer",
                    ),
                )

        optimizer_classes = [
            opt
            for opt in torch.optim.__dict__.values()
            if inspect.isclass(opt) and issubclass(opt, torch.optim.Optimizer)
        ]

        # Note: we don't support sparsity or tracing through backwards
        excluded_optimizer_classes = {
            torch.optim.SparseAdam,
            torch.optim.LBFGS,
        }

        for opt in optimizer_classes:
            if opt in excluded_optimizer_classes:
                opt.step = disable(
                    opt.step, reason=f"optimizer {opt} step not supported"
                )

            if hasattr(opt, "_init_group"):
                opt._init_group = disable(
                    opt._init_group, reason=f"optimizer {opt} _init_group not supported"
                )
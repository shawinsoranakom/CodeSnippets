def _collect_tensors_with_sources(
    var: VariableTracker,
) -> list[tuple[torch.Tensor, str | None]]:
    """Extract (fake_tensor, source_name) pairs from a VariableTracker.

    Used by handle_autograd_grad to collect tensors from the outputs and inputs
    arguments for grad_fn reachability analysis.
    """
    from torch.utils._python_dispatch import is_traceable_wrapper_subclass

    from .lazy import LazyVariableTracker
    from .lists import BaseListVariable
    from .tensor import TensorVariable

    results: list[tuple[torch.Tensor, str | None]] = []
    if isinstance(var, TensorVariable):
        fake_tensor = var.as_proxy().node.meta.get("example_value")
        assert isinstance(fake_tensor, torch.Tensor)
        if isinstance(fake_tensor, torch._subclasses.fake_tensor.FakeTensor):
            pass
        elif is_traceable_wrapper_subclass(fake_tensor):
            # For tensor subclasses (e.g. DTensor), verify the inner tensors
            # are FakeTensors but keep the original subclass for grad_fn
            # reachability analysis.
            plain: list[object] = []
            torch._subclasses.fake_tensor.get_plain_tensors(
                fake_tensor,  # pyrefly: ignore[bad-argument-type]
                out=plain,  # pyrefly: ignore[bad-argument-type]
            )
            assert all(
                isinstance(t, torch._subclasses.fake_tensor.FakeTensor)
                for t in plain
                if isinstance(t, torch.Tensor)
            ), (
                f"Expected all plain tensors to be FakeTensors, got {[type(t) for t in plain]}"
            )
        else:
            raise AssertionError(
                f"Expected FakeTensor or subclass, got {type(fake_tensor)}"
            )
        source_name = var.source.name if var.source else None
        results.append((fake_tensor, source_name))
    elif isinstance(var, LazyVariableTracker):
        # Realize the lazy var to get the actual TensorVariable
        results.extend(_collect_tensors_with_sources(var.realize()))
    elif isinstance(var, BaseListVariable):
        for item in var.items:
            results.extend(_collect_tensors_with_sources(item))
    else:
        unimplemented(
            gb_type="autograd.grad with unsupported argument type",
            context=f"got {type(var).__name__}",
            explanation=(
                f"torch.autograd.grad() received an argument of type {type(var).__name__} "
                "which is not supported. Expected tensor or sequence of tensors."
            ),
            hints=[
                "Ensure outputs and inputs arguments are tensors or sequences of tensors.",
            ],
        )
    return results
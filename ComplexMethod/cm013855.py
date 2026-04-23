def raise_jump_graph_break(value: VariableTracker) -> NoReturn:
        trace_info = format_tensor_computation_trace(value)
        hints: list[str] = []
        if isinstance(value, TensorVariable):
            try:
                node = value.proxy.node
                example = node.meta.get("example_value")
                if (
                    example is not None
                    and example.dim() == 0
                    and example.dtype
                    in (
                        torch.int32,
                        torch.int64,
                    )
                ):
                    hints.append(
                        "The branch condition uses a scalar integer tensor. "
                        "Consider rewriting the computation to use plain Python "
                        "ints (e.g. use int attributes instead of tensor buffers) "
                        "so the condition becomes a shape guard instead of "
                        "data-dependent branching."
                    )
                if (
                    example is not None
                    and example.dim() == 0
                    and example.dtype == torch.bool
                ):
                    hints.append(
                        "For the common pattern `if tensor_cond: x = transform(x)` "
                        "(e.g. clamping inf/nan values), consider making the code "
                        "branchless by always applying the transform. Operations like "
                        "torch.clamp, torch.nan_to_num, and torch.where are typically "
                        "no-ops on well-behaved inputs and compile without graph breaks."
                    )
                # Detect boolean reductions (any/all) which are a telltale sign
                # of `tensor.any() or other_tensor.any()` patterns.
                # node.target is a str for call_method nodes (e.g. tensor.any())
                # and a callable for call_function nodes (e.g. torch.any()).
                target_name = getattr(node.target, "__name__", None) or (
                    node.target if isinstance(node.target, str) else None
                )
                if target_name in ("any", "all", "bitwise_and", "bitwise_or"):
                    hints.append(
                        "Note: Python `or`/`and` between tensor expressions (e.g. "
                        "`tensor.any() or other_tensor.any()`) triggers implicit bool "
                        "conversion. Use `torch.logical_or`/`torch.logical_and` or the "
                        "`|`/`&` operators instead."
                    )
            except Exception:
                pass
        hints.extend(graph_break_hints.FUNDAMENTAL)
        hints.append("Use `torch.cond` to express dynamic control flow.")
        unimplemented(
            gb_type="Data-dependent branching",
            context=f"attempted to jump with {value}",
            explanation="Detected data-dependent branching (e.g. `if my_tensor.sum() > 0:`). "
            "Dynamo does not support tracing dynamic control flow." + trace_info,
            hints=hints,
        )
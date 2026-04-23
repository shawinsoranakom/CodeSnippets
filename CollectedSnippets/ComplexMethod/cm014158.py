def _comparison_with_tensor(
        self, tx: "InstructionTranslator", left: VariableTracker, right: VariableTracker
    ) -> VariableTracker:
        from .builder import wrap_fx_proxy_cls
        from .tensor import supported_tensor_comparison_op_values

        op = self.fn

        if op in [operator.is_, operator.is_not]:
            is_result = (
                left.is_tensor()
                and right.is_tensor()
                and id(extract_fake_example_value(left.as_proxy().node))
                == id(extract_fake_example_value(right.as_proxy().node))
            )
            if op is operator.is_:
                return VariableTracker.build(tx, is_result)
            else:
                return VariableTracker.build(tx, not is_result)

        if op not in supported_tensor_comparison_op_values:
            unimplemented(
                gb_type="unsupported Tensor comparison op",
                context=f"{op.__name__}({left}, {right})",
                explanation=f"Dynamo does not support the comparison op {op.__name__} "
                f"with Tensor arguments {left}, {right}",
                hints=[*graph_break_hints.SUPPORTABLE],
            )
        if (
            isinstance(left, TensorVariable)
            and isinstance(right, TensorVariable)
            and (left.size and right.size) is not None
            and left.size != right.size
        ):
            try:
                torch.broadcast_shapes(left.size, right.size)
            except RuntimeError:
                # not broadcastable, can't be compared
                unimplemented(
                    gb_type="failed to broadcast when attempting Tensor comparison op",
                    context=f"{op.__name__}({left}, {right})",
                    explanation=f"Dynamo was unable to broad cast the arguments {left}, {right} "
                    f"when attempting to trace the comparison op {op.__name__}.",
                    hints=[*graph_break_hints.USER_ERROR],
                )
        tensor_cls = left if left.is_tensor() else right
        proxy = tx.output.create_proxy(
            "call_function", op, (left.as_proxy(), right.as_proxy()), {}
        )
        return wrap_fx_proxy_cls(
            type(tensor_cls),  # handle Ndarrays and Tensors
            tx,
            proxy,
        )
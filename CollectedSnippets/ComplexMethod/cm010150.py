def call_function(
            self,
            target: torch.fx.node.Target,
            args: tuple[Argument, ...],
            kwargs: dict[str, Argument],
        ) -> ProxyValue:
            meta = NodeMetadata(self.node.meta)

            if target is operator.getitem:
                value, key = args
                return self.callback.call_getitem(value, key, meta)
            elif getattr(target, "__module__", None) in {
                "_operator",
                "builtins",
                "math",
            }:
                if not callable(target):
                    raise AssertionError(f"expected callable target, got {target}")
                return self.callback.call_sym(target, args, meta)
            elif target in _TORCH_SYM_OPS:
                if not callable(target):
                    raise AssertionError(f"expected callable target, got {target}")
                return self.callback.call_sym(target, args, meta)
            elif isinstance(
                target, (torch._ops.OpOverload, torch._ops.OpOverloadPacket)
            ):
                return self.callback.call_operator(
                    target,
                    args,
                    kwargs,
                    meta,
                )
            elif target is torch.ops.higher_order.cond:
                pred, true_fn, false_fn, inputs = args
                return self.callback.call_cond(pred, true_fn, false_fn, inputs, meta)
            elif target is torch.ops.higher_order.map_impl:
                f, mapped_args, operands = args  # type: ignore[assignment]
                return self.callback.call_map(f, mapped_args, operands, meta)
            # For other unregistered HigherOrderOps, just interpret them blindly
            elif isinstance(target, torch._ops.HigherOrderOperator):
                return self.callback._fx(
                    "call_function",
                    target,
                    args,
                    kwargs,
                    meta,
                )
            else:
                raise ExportPassBaseError(f"Unsupported target type: {target}")
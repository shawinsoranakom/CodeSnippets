def any_input_has_multi_consumers() -> bool:
            current_node = V.current_node
            if current_node is None:
                return False
            fx_args = current_node.args[0]
            if isinstance(fx_args, (list, tuple)):
                input_nodes = fx_args
            elif isinstance(fx_args, torch.fx.Node):
                input_nodes = [fx_args]
            else:
                return False

            def is_unrealized_pointwise(x):
                if isinstance(x, (TensorBox, ir.StorageBox)):
                    return is_unrealized_pointwise(unwrap_tensor(x))
                return isinstance(x, ir.Pointwise)

            for arg, ir_input in zip(input_nodes, inputs):
                if not hasattr(arg, "users") or len(arg.users) <= 1:
                    continue
                # input will be computed multiple times because other consumers
                # (eg. pointwise) will also inline it. So we should realize-in-place via ConcatKernel
                if any(is_pointwise_use(u) for u in arg.users if u is not current_node):
                    return True
                # If input is an unrealized Pointwise with multiple consumers, pointwise_cat
                # will inline input without realizing it to memory, causing separate
                # realization cost for input. So we should realize-in-place via ConcatKernel
                if is_unrealized_pointwise(ir_input):
                    return True
            return False
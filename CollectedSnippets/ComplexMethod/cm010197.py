def deserialize_node(self, serialized_node: Node, target: Callable) -> None:
        def _is_single_tensor_return(target) -> bool:
            schema = _get_schema_from_target(target)
            returns = schema.returns
            return len(returns) == 1 and isinstance(
                returns[0].real_type, torch.TensorType
            )

        if (
            target in _SYM_OPS
            or target
            == torch.ops.aten.item.default  # this can produce either SymInt or SymBool
        ):
            # BC: use serialized_node.name if available, otherwise fallback to original logic
            name = (
                serialized_node.name
                if serialized_node.name
                else serialized_node.outputs[0].value.as_name
            )
            args = self.deserialize_sym_op_inputs(serialized_node.inputs)

            fx_node = self.graph.create_node("call_function", target, args, {}, name)
            self.deserialize_sym_op_outputs(serialized_node, fx_node)
        elif (
            target
            is torch._higher_order_ops.triton_kernel_wrap.triton_kernel_wrapper_functional
        ):
            raise SerializeError(
                "deserialize nyi for torch._higher_order_ops.triton_kernel_wrap.triton_kernel_wrapper_functional"
            )
        elif isinstance(target, torch._ops.HigherOrderOperator):
            args, kwargs = self.deserialize_hoo_inputs(serialized_node.inputs)
            metadata = self.deserialize_metadata(serialized_node.metadata)
            for x in (*args, *kwargs.values()):
                if isinstance(x, torch.fx.Node) and x.op == "get_attr":
                    # this means that we have deserialized a graph argument, but
                    # unfortunately the schema for it does not include metadata;
                    # so we reuse the metadata of the HOP call for such arguments
                    x.meta.update(metadata)
            # If a serialized HOP node has a length=1 outputs of type `as_tensor``.
            # There could be two cases:
            # (1) The HOP node returns a single tensor
            # (2) The HOP node returns a tuple containing a single tensor
            # We distinguish (1) and (2) by the `is_single_tensor_return`
            # field in the schema of Node
            # For BC, getattr() will return True if `is_single_tensor_return` doesn't
            # exist. This is because prior to adding `is_single_tensor_return`,
            # only (1) could happen as we handle (2) with type `as_tensors`
            # BC: use serialized_node.name if available, otherwise fallback to original logic
            if serialized_node.name:
                name = serialized_node.name
            else:
                name = (
                    serialized_node.outputs[0].as_tensor.name
                    if len(serialized_node.outputs) == 1
                    and hasattr(serialized_node.outputs[0], "as_tensor")
                    and getattr(serialized_node, "is_hop_single_tensor_return", True)
                    else None
                )
            fx_node = self.graph.create_node(
                "call_function", target, args, kwargs, name
            )
            self.deserialize_outputs(serialized_node, fx_node)
            fx_node.meta.update(metadata)

        elif isinstance(
            target, (torch._ops.OpOverload, *_registered_extension_types())
        ):
            # For convenience: if this node returns a single tensor, name the
            # newly-created node after it. This ensures that these tensor values
            # have names that are consistent with serialized.
            # BC: use serialized_node.name if available, otherwise fallback to original logic
            if serialized_node.name:
                name = serialized_node.name
            else:
                name = (
                    serialized_node.outputs[0].as_tensor.name
                    if _is_single_tensor_return(target)
                    else None  # FX will generate a name for us.
                )

            args, kwargs = self.deserialize_inputs(target, serialized_node)
            fx_node = self.graph.create_node(
                "call_function", target, args, kwargs, name
            )
            self.deserialize_outputs(serialized_node, fx_node)
        else:
            _additional_msg = (
                (
                    f"We failed to resolve {target} to an operator. "
                    + "If it's a custom op/custom triton op, this is usually because the custom op is not registered"
                    + " when deserializing. Please import the custom op to register it before deserializing."
                    + " Otherwise, please file an issue on github."
                )
                if isinstance(target, str)
                else ""
            )
            raise SerializeError(
                _additional_msg
                + f" Unsupported target type for node {serialized_node}: {type(target)}."
            )

        fx_node.meta.update(self.deserialize_metadata(serialized_node.metadata))
        log.debug(
            "[deserialize_node] %s: %s(%s, {%s}) -> %s",
            fx_node.name,
            fx_node.target,
            fx_node.args,
            fx_node.kwargs,
            fx_node.meta.get("val"),
        )

        # handle ShapeEnv asserts
        if target is torch.ops.aten._assert_scalar.default:
            if not isinstance((arg := fx_node.args[0]), bool):
                expr = arg.meta["val"]  # type: ignore[union-attr]
                if isinstance(expr, torch.SymBool):
                    self.shape_env.guard_or_defer_runtime_assert(
                        expr.node.expr, "", fx_node
                    )
        elif target is torch.ops.aten.sym_constrain_range_for_size.default:
            sym = fx_node.args[0].meta["val"]  # type: ignore[union-attr]
            if isinstance(sym, torch.SymInt):
                self.shape_env._constrain_range_for_size(sym.node.expr)

        # handle nn_module_stack; serialization throws away empty dicts
        if (
            fx_node.op not in ["placeholder", "output"]
            and "nn_module_stack" not in fx_node.meta
        ):
            fx_node.meta["nn_module_stack"] = {}
def handle_call_function(self, node: torch.fx.Node):
        if node.op != "call_function":
            raise AssertionError(f"expected call_function op, got {node.op}")
        meta_val = node.meta.get("val")
        log.debug(
            "[handle_call_function] %s: %s(%s, {%s}) -> %s",
            node.name,
            node.target,
            node.args,
            node.kwargs,
            meta_val,
        )

        # getitem has been handled in the producer node, skip it here
        if node.target is operator.getitem:
            return

        if node.target in _SYM_OPS or (
            meta_val is not None
            and isinstance(meta_val, (torch.SymInt, torch.SymBool, torch.SymFloat))
        ):
            if len(node.kwargs) != 0:
                raise AssertionError(
                    f"expected no kwargs for sym op, got {len(node.kwargs)}"
                )
            ex_node = Node(
                name=node.name,
                target=self.serialize_operator(node.target),
                inputs=self.serialize_sym_op_inputs(node.target, node.args),
                outputs=[self.serialize_output(node.name, meta_val)],
                metadata=self.serialize_metadata(node),
            )
        elif isinstance(node.target, torch._ops.OpOverload):
            ex_node = Node(
                name=node.name,
                target=self.serialize_operator(node.target),
                inputs=self.serialize_inputs(node.target, node.args, node.kwargs),
                outputs=self.serialize_outputs(node),
                # TODO: create a new tensor_values here, meta might have faketensor info
                metadata=self.serialize_metadata(node),
            )
        elif isinstance(node.target, torch._ops.HigherOrderOperator):

            def _is_hop_single_tensor_return(node) -> bool:
                if not isinstance(node.target, torch._ops.HigherOrderOperator):
                    raise AssertionError(
                        f"expected HigherOrderOperator, got {type(node.target).__name__}"
                    )
                # HOP schema is not always available, so we look at node.meta["val"]
                meta_val = node.meta.get("val", None)
                return meta_val is not None and isinstance(meta_val, torch.Tensor)

            # Special handle serialization for aoti_call_delegate
            if node.target is torch._higher_order_ops.aoti_call_delegate:
                serializable_args = list(node.args)

                # AOTI lowered module is not serializable, serialize the aoti_path instead
                lowered_module_name: str = node.args[0].name  # type: ignore[assignment, no-untyped-def, union-attr]
                if not hasattr(node.graph.owning_module, lowered_module_name):
                    raise AssertionError(
                        f"owning_module does not have attribute {lowered_module_name}"
                    )
                lowered_module = getattr(node.graph.owning_module, lowered_module_name)  # type: ignore[no-untyped-def]
                serializable_args[0] = lowered_module.aoti_path

                # AOTI compiled graph module in node.args[0] is stateful, and will fail the verifier check
                # Skip serializing original_gm as a workaround
                serializable_args[1] = None

                serializable_weight_nodes = []
                if serializable_args[2] is not None and isinstance(
                    serializable_args[2], Iterable
                ):
                    for weight_node in serializable_args[2]:
                        # skip passing custom obj into the weight arg as an hack
                        # The schema of weight input is a list of Tensors.
                        # Downstream runtime is not actively consuming the weighs arg for anything meaningful.
                        if isinstance(weight_node, torch.fx.Node) and isinstance(
                            weight_node.meta.get("val", None), ep.CustomObjArgument
                        ):
                            continue
                        serializable_weight_nodes.append(weight_node)
                    serializable_args[2] = serializable_weight_nodes

                def serialize_tensor_list_output(node):
                    meta_val = node.meta.get("val", None)
                    tensor_args = []
                    for idx, meta in enumerate(meta_val):
                        name = self._output_node_name_at_index(node, idx)
                        tensor_args.append(self.serialize_tensor_output(name, meta))
                    return [Argument.create(as_tensors=tensor_args)]

                ex_node = Node(
                    name=node.name,
                    target=self.serialize_operator(node.target),
                    inputs=self.serialize_hoo_inputs(serializable_args, node.kwargs),
                    outputs=serialize_tensor_list_output(node),
                    metadata=self.serialize_metadata(node),
                    is_hop_single_tensor_return=False,
                )
            elif (
                node.target
                is torch._higher_order_ops.triton_kernel_wrap.triton_kernel_wrapper_functional
            ):
                kernel, kernel_cache_entry = get_triton_kernel_and_cache_entry(node)
                kernel_cache_metadata = kernel_cache_entry.metadata

                meta_val = node.meta["val"]
                if not isinstance(meta_val, dict):
                    raise AssertionError(
                        f"expected meta_val to be dict, got {type(meta_val).__name__}"
                    )

                output_keys = meta_val.keys()
                output_indices = []

                constexpr_keys = {p.name for p in kernel.params if p.is_constexpr}
                found_constexpr = False
                args_new = ()
                i = 0

                if not isinstance(node.kwargs["kwargs"], dict):
                    raise AssertionError(
                        f"expected kwargs['kwargs'] to be dict, got {type(node.kwargs['kwargs'])}"
                    )
                for k, v in node.kwargs["kwargs"].items():
                    # don't serialize constexpr since they will
                    # be embedded into the binary and don't
                    # need to be passed around as attributes
                    if k in constexpr_keys:
                        found_constexpr = True
                        continue

                    if found_constexpr:
                        raise AssertionError(
                            "non-constexpr args found after constexpr arg(s)"
                        )

                    if k in output_keys:
                        output_indices.append(i)
                    args_new += (v,)  # type: ignore[assignment]
                    i += 1

                if not isinstance(node.kwargs["grid"], list):
                    raise AssertionError(
                        f"expected grid to be list, got {type(node.kwargs['grid'])}"
                    )

                kernel_name_with_hash = (
                    f"{kernel.fn.__name__}_{kernel_cache_metadata.hash}"
                )
                kwargs_new = {
                    "name": kernel_name_with_hash,
                    "grid": node.kwargs["grid"][0],
                    "output_indices": output_indices,
                    "num_warps": kernel_cache_metadata.num_warps,
                }
                if hasattr(kernel_cache_metadata, "num_cpu_threads"):
                    kwargs_new["num_cpu_threads"] = (
                        kernel_cache_metadata.num_cpu_threads
                    )

                if hasattr(kernel_cache_metadata, "shared"):
                    if isinstance(kernel_cache_metadata.shared, bool):
                        kwargs_new["shared_memory_bytes"] = int(
                            kernel_cache_metadata.shared
                        )
                    else:
                        kwargs_new["shared_memory_bytes"] = kernel_cache_metadata.shared

                # MTIA-specific parameters for triton kernel compilation
                if hasattr(kernel_cache_metadata, "tile_width"):
                    kwargs_new["tile_width"] = kernel_cache_metadata.tile_width
                if hasattr(kernel_cache_metadata, "tile_height"):
                    kwargs_new["tile_height"] = kernel_cache_metadata.tile_height
                if hasattr(kernel_cache_metadata, "base_pe"):
                    kwargs_new["base_pe"] = kernel_cache_metadata.base_pe

                # Kernel parameter metadata for MTIA fatbin compilation
                kwargs_new["kernel_param_names"] = [
                    p.name for p in kernel.params if not p.is_constexpr
                ]
                # Use inferred signature types from the compiled kernel's ASTSource
                # when available. The signature is populated at runtime with actual
                # types like "i32", "*fp32" based on the values passed to the kernel
                # (see specialize_impl in jit.py). Fall back to static annotations
                # for architectures that don't rely on precise type information.
                compiled_signature = getattr(
                    getattr(kernel_cache_entry, "src", None), "signature", None
                )
                if compiled_signature is not None:
                    kwargs_new["kernel_param_types"] = [
                        str(compiled_signature.get(p.name, p.annotation))
                        for p in kernel.params
                        if not p.is_constexpr
                    ]
                else:
                    # Default behavior: use static annotations (may be empty)
                    kwargs_new["kernel_param_types"] = [
                        str(p.annotation) for p in kernel.params if not p.is_constexpr
                    ]

                ex_node = Node(
                    name=node.name,
                    target=self.serialize_operator(node.target),
                    inputs=self.serialize_hoo_inputs(args_new, kwargs_new),
                    outputs=self.serialize_hoo_outputs(node),
                    metadata=self.serialize_metadata(node),
                    is_hop_single_tensor_return=_is_hop_single_tensor_return(node),
                )
            else:
                ex_node = Node(
                    name=node.name,
                    target=self.serialize_operator(node.target),
                    inputs=self.serialize_hoo_inputs(node.args, node.kwargs),
                    outputs=self.serialize_hoo_outputs(node),
                    metadata=self.serialize_metadata(node),
                    is_hop_single_tensor_return=_is_hop_single_tensor_return(node),
                )
        elif type(node.target) in _serialization_registry:
            # Sanity check for unhandled serialization.
            if type(node.target) not in _serialization_registry:
                raise AssertionError(
                    f"{type(node.target)} is not supported in export serialization."
                )

            handler = _serialization_registry[type(node.target)]
            namespace = handler.namespace()
            op_name = handler.to_op_name(node.target)
            if not isinstance(namespace, str) or not isinstance(op_name, str):
                raise AssertionError(
                    f"expected namespace and op_name to be str, got {type(namespace).__name__} and {type(op_name).__name__}"
                )
            if ":" in namespace or ":" in op_name:
                raise AssertionError(
                    f"namespace and op_name should not contain ':', got {namespace!r} and {op_name!r}"
                )
            ex_node = Node(
                name=node.name,
                target=f"#{namespace}:{op_name}",
                inputs=self.serialize_inputs(node.target, node.args, node.kwargs),
                outputs=self.serialize_outputs(node),
                metadata=self.serialize_metadata(node),
            )
        else:
            raise SerializeError(f"Serializing {node.target} is not supported")

        self.graph_state.nodes.append(ex_node)
def add_to_dtype(sub_graph: torch.fx.Graph):
            def get_input_dtype(node: torch.fx.Node) -> torch.dtype | None:
                """Get input dtype for nodes that may consumes lowp fp dt"""
                if node.target == "store":
                    return V.graph.get_dtype(node.args[1])  # type: ignore[arg-type]
                elif node.target == "to_dtype_bitcast":
                    return node.args[-1]  # type: ignore[return-value]
                elif node.target == "to_dtype":
                    if len(node.args) > 3:
                        return node.args[3]  # type: ignore[return-value]
                    else:
                        return node.kwargs.get("src_dtype", None)  # type: ignore[return-value]
                else:
                    return None

            def get_output_dtype(node: torch.fx.Node) -> torch.dtype | None:
                """Get output dtype for nodes that may produce lowp fp dt"""
                if node.target == "load":
                    assert len(node.args) == 3
                    return V.graph.get_dtype(node.args[1])  # type: ignore[arg-type]
                elif node.target in ["to_dtype", "constant", "index_expr"]:
                    return node.args[-1]  # type: ignore[return-value]
                elif node.target == "to_dtype_bitcast":
                    return node.args[2]  # type: ignore[return-value]
                else:
                    return None

            def is_lowp_fp_source(node: torch.fx.Node, dt: torch.dtype):
                """Check if the given node produces output with expected low precision floating point data type."""
                assert dt in DTYPE_LOWP_FP
                return get_output_dtype(node) == dt

            def is_lowp_fp_sink(node: torch.fx.Node, dt: torch.dtype):
                """Check if the given node accept input with expected low precision floating point data type."""
                assert dt in DTYPE_LOWP_FP
                if input_dtype := get_input_dtype(node):
                    return input_dtype == dt
                elif node.target == "to_dtype":
                    # The `src_dtype` of a `to_dtype` node might miss, in which case the node accept any input dtype.
                    return True
                else:
                    return False

            def is_lowp_fp_source_no_promote(node: torch.fx.Node, dt: torch.dtype):
                """Check if the node is a lowp fp sources which are all directly fed to ops that accepts lowp fp input
                thus no need to promote to float
                """
                return is_lowp_fp_source(node, dt) and all(
                    is_lowp_fp_sink(user, dt) for user in node.users
                )

            sub_graph_nodes = list(sub_graph.nodes)
            to_lowp_fp_legalized_nodes = []
            for _node in sub_graph_nodes:
                if (
                    _node.target in ["load", "index_expr"]
                    and (dt := get_output_dtype(_node)) in DTYPE_LOWP_FP
                ):
                    # No need to promote to float if all users are ops that accepts lowp fp input
                    # pyrefly: ignore [bad-argument-type]
                    if all(is_lowp_fp_sink(user, dt) for user in _node.users):
                        continue
                    ops = _node.args[0]
                    with sub_graph.inserting_after(_node):
                        to_type_node = sub_graph.call_method(
                            "to_dtype", args=(ops, _node, torch.float)
                        )
                        _node.replace_all_uses_with(
                            to_type_node, lambda n: n is not to_type_node
                        )
                        # pyrefly: ignore [bad-assignment]
                        metrics.cpp_to_dtype_count += 1
                elif (
                    _node.target == "store"
                    and (dt := get_input_dtype(_node)) in DTYPE_LOWP_FP
                ):
                    ops, name, _, value_var, _ = _node.args
                    # pyrefly: ignore [bad-argument-type]
                    if is_lowp_fp_source_no_promote(value_var, dt):
                        continue
                    dtype = V.graph.get_dtype(name)
                    with sub_graph.inserting_before(_node):
                        to_type_node = sub_graph.call_method(
                            "to_dtype", args=(ops, value_var, dtype)
                        )
                        _node.replace_input_with(value_var, to_type_node)
                        # pyrefly: ignore [bad-assignment]
                        metrics.cpp_to_dtype_count += 1
                elif _node.target == "reduction":
                    (
                        ops,
                        dtype,
                        src_dtype,
                        reduction_type,
                        value,
                    ) = _node.args
                    if src_dtype in DTYPE_LOWP_FP:
                        # Since we always convert the load/store value to float if the tensor is bfloat16/float16.
                        # Therefore, the reduction should never work with bfloat16/float16 value. Hence, we update
                        # the bfloat16/float16 reduction by
                        #     1) updating the src_dtype to float
                        # and 2) updating the dtype to float if it is bfloat16/float16.
                        assert dtype in [
                            torch.float,
                            torch.bfloat16,
                            torch.float16,
                            torch.int64,
                        ]
                        _node.args = (
                            ops,
                            torch.float if dtype in DTYPE_LOWP_FP else dtype,
                            torch.float,
                            reduction_type,
                            value,
                        )
                elif _node.target == "constant" and _node.args[-1] in DTYPE_LOWP_FP:
                    # No need to promote to float if all users are ops that accepts lowp fp input
                    (ops, value, dt) = _node.args
                    if all(is_lowp_fp_sink(user, dt) for user in _node.users):  # type: ignore[arg-type]
                        continue
                    _node.args = (ops, value, torch.float)
                elif _node.target == "to_dtype" and _node.args[-1] in DTYPE_LOWP_FP:
                    # No need to promote to float if all users are ops that accepts lowp fp input
                    (ops, x, dt) = _node.args
                    if all(is_lowp_fp_sink(user, dt) for user in _node.users):  # type: ignore[arg-type]
                        continue
                    # The legalization always loads the BF16/FP16 tensor as FP32 for computation
                    # and converts back to BF16/FP16 after the computation.
                    # Hence, there should be no computation w/ BF16/FP16.
                    # Therefore, we update the to_dtype by replacing the bf16/fp16 dtype with fp32.
                    # Save the legalized to_dtype node for the elimination(eliminate_to_dtype step):
                    #  1) Eliminate the redundant to_dtype node if we have a pattern as follows:
                    #     graph():
                    #       %lowp_fp_legalized = call_method[target=to_dtype](args = (%ops, %input, torch.float))
                    #       %to_dtype2 = call_method[target=to_dtype](args = (%ops, %lowp_fp_legalized, torch.bfloat16/float16))
                    # Regarding the first to_dtype, it is redundant because
                    # the second to_type also converts to the torch.bfloat16/torch.float16.
                    # Hence, we remove the first to_type.
                    to_lowp_fp_legalized_nodes.append(_node)
                    _node.args = (ops, x, torch.float)
                elif _node.target == "to_dtype_bitcast":
                    (ops, value_var, dtype, src_dtype) = _node.args

                    # to_dtype_bitcast act as a lowp fp sink:
                    # c10::bit_cast requires the source and target have the same bitwidth. Because the input tensor's
                    # dtype could be promoted, e.g. from float16 to float, we have to cast the tensor to its original
                    # source dtype before invoking bit_cast.
                    if src_dtype in DTYPE_LOWP_FP:
                        # No need to promote to float if it is a user of a lowp fp sources
                        # which are all directly fed to ops that accepts lowp fp input
                        if not is_lowp_fp_source_no_promote(value_var, src_dtype):
                            with sub_graph.inserting_before(_node):
                                to_type_node = sub_graph.call_method(
                                    "to_dtype", args=(ops, value_var, src_dtype)
                                )
                                _node.replace_input_with(value_var, to_type_node)
                                # pyrefly: ignore [bad-assignment]
                                metrics.cpp_to_dtype_count += 1

                    # to_dtype_bitcast act as a lowp fp source:
                    # We also need to convert the bit-casted tensor back to float to make sure we keep using higher
                    # precision values for the rest of the computation.
                    if dtype in DTYPE_LOWP_FP:
                        # No need to promote to float if all users are ops that accepts lowp fp input
                        if not (
                            all(is_lowp_fp_sink(user, dtype) for user in _node.users)
                        ):
                            ops = _node.args[0]
                            with sub_graph.inserting_after(_node):
                                to_type_node = sub_graph.call_method(
                                    "to_dtype", args=(ops, _node, torch.float)
                                )
                                _node.replace_all_uses_with(
                                    to_type_node, lambda n: n is not to_type_node
                                )
                                # pyrefly: ignore [bad-assignment]
                                metrics.cpp_to_dtype_count += 1

            def eliminate_to_dtype(sub_graph: torch.fx.Graph):
                def _eliminate_duplicate_to_node(sub_graph: torch.fx.Graph):
                    # Eliminate the redundant to_dtype node. Let's consider a pattern as follows:
                    #   graph():
                    #     %to_dtype1 = call_method[target=to_dtype](args = (%ops, %input, torch.float), kwargs = {})
                    #     %to_dtype2 = call_method[target=to_dtype](args = (%ops, %to_dtype1, torch.float), kwargs = {})
                    # Regarding the first to_dtype, it is redundant because the second to_type also converts to the
                    # torch.float. Hence, we remove the first to_type
                    def _used_by_to(to_node: torch.fx.Node):
                        return all(usr.target == "to_dtype" for usr in to_node.users)

                    all_to_nodes = [
                        node for node in sub_graph.nodes if node.target == "to_dtype"
                    ]
                    all_to_nodes_and_users = [
                        {node: node.users} for node in all_to_nodes if _used_by_to(node)
                    ]
                    for node_users in all_to_nodes_and_users:
                        for node, users in node_users.items():
                            if node in sub_graph.nodes and (
                                all(usr.args[-1] == node.args[-1] for usr in users)
                                or (
                                    node in to_lowp_fp_legalized_nodes
                                    and all(
                                        usr.args[-1] in DTYPE_LOWP_FP for usr in users
                                    )
                                )
                            ):
                                val_node = node.all_input_nodes[-1]
                                node.replace_all_uses_with(val_node)
                                sub_graph.erase_node(node)

                    # For debug mode, the graph of LoopBody will attach a new GraphModule as
                    # owning_module for debugging while the release mode will not. The lint will
                    # check whether the graph has owning_module to decide if it needs to check
                    # call_module. LoopBody might contain get_index as a module call. But it
                    # is just a function. Hence, it cannot pass the lint check for debug mode.
                    # We bypass the check if the owning_module is None. Eventually, we should call
                    # get_index via call_function but not call_module.
                    if sub_graph.owning_module is None:
                        sub_graph.lint()

                _eliminate_duplicate_to_node(sub_graph)

            eliminate_to_dtype(sub_graph)
def maybe_inline_graph_saved_tensors_hooks(
    fw_module: torch.fx.GraphModule,
    bw_module: torch.fx.GraphModule,
    num_inner_fwd_outputs: int,
    inner_meta: ViewAndMutationMeta,
    aot_config: AOTConfig,
    static_input_indices: list[int],
) -> None:
    if torch._dynamo.compiled_autograd.in_compiled_autograd_region:
        return

    get_hooks = torch._functorch._aot_autograd.utils.top_saved_tensors_hooks
    are_inline_hooks = (
        torch._functorch._aot_autograd.utils.saved_tensors_hooks_are_inlineable
    )

    hooks = get_hooks()
    if not are_inline_hooks(hooks):
        return

    pack_hook_gm, unpack_hook_gm = hooks

    structured_logs: list[str] = []
    maybe_log_graph(
        fw_module,
        "Forward graph pre saved_tensors_hooks inlining",
        aot_config,
        lambda: "aot_forward_graph_pre_saved_tensors_hooks",
        structured_logs,
    )
    maybe_log_graph(
        bw_module,
        "Backward graph pre saved_tensors_hooks inlining",
        aot_config,
        lambda: "aot_backward_graph_pre_saved_tensors_hooks",
        structured_logs,
    )
    fw_g = fw_module.graph
    bw_g = bw_module.graph

    fw_g_names = {node.name for node in fw_g.nodes}
    bw_g_names = {node.name for node in bw_g.nodes}

    def _gen_unused_name(candidate: str) -> str:
        c = candidate
        i = 0
        while c in fw_g_names or c in bw_g_names:
            c = f"{candidate}_{i}"
            i = i + 1
        return c

    bw_g_inputs = bw_g.find_nodes(op="placeholder")

    fw_out_n = fw_g.output_node()
    fw_outs = fw_out_n.args[0]  # type: ignore[var-annotated]
    fw_outs_inner_set = set(fw_outs[:num_inner_fwd_outputs])  # type: ignore[index]
    fw_outs_saved_for_bw = fw_outs[num_inner_fwd_outputs:]  # type: ignore[index]
    fw_outs_packed_tensors = []  # type: ignore[var-annotated]
    fw_outs_packed_syms = []  # type: ignore[var-annotated]

    # The main use case for saved_tensors_hooks is activation quantization,
    # for memory usage optimization.
    # Desired behavior is to quantize saved activations to free the original saved tensor.
    # Saved nodes may include forward inputs, outputs, parameters.
    # They may be held by something else and will not be deallocated after quantization.
    # Donated buffers are intermediates in the graph invisible for the user,
    # this guarantees that they can be deallocated.
    # Using this as a default behavior to select saved nodes to apply hooks.
    # There is also a config to apply hooks for all saved nodes without any filtering.
    # The plan is to propagate meta about the source of the saved node to the user hook function.
    mode = torch._functorch.config.saved_tensors_hooks_filtering_mode
    allow_set = None
    exclude_set = None

    if mode == "donated":
        # collect_bw_donated_buffer_idxs requires inner_meta to have num_symints_saved_for_bw
        inner_meta.num_symints_saved_for_bw = len(
            [n for n in fw_outs_saved_for_bw if is_sym_node(n)]  # type: ignore[arg-type]
        )
        # Count tensors with no version counter check (used in tensors_saved_for_backwards_slice)
        inner_meta.num_tensors_saved_with_no_vc_check = len(
            [
                n
                # pyrefly: ignore [not-iterable]
                for n in fw_outs_saved_for_bw
                if isinstance(n, torch.fx.Node)
                and n.meta.get("saved_tensor_with_no_vc_check", False)
            ]
        )
        bw_donated_idxs = collect_bw_donated_buffer_idxs(
            fw_module,
            bw_module,
            inner_meta,
        )
        fw_donated_idxs = [
            i - inner_meta.num_symints_saved_for_bw for i in bw_donated_idxs
        ]
        allow_set = {fw_outs_saved_for_bw[i].name for i in fw_donated_idxs}  # type: ignore[union-attr]
    elif mode == "no_static":
        fw_g_inputs = fw_g.find_nodes(op="placeholder")
        exclude_set = {fw_g_inputs[i].name for i in static_input_indices}

    if (allow_set is not None) and (not allow_set):
        # This means we have empty whitelist,
        # No donated (intermediate) saved.
        # Do not do anything in this case
        return

    if aot_config.enable_log:
        structured_logs.append(f"fw_outs_saved_for_bw:{fw_outs_saved_for_bw}")
        structured_logs.append(f"mode:{mode}")
        structured_logs.append(f"allow_set:{allow_set}")
        structured_logs.append(f"exclude_set:{exclude_set}")

    # pyrefly: ignore [not-iterable]
    for saved in fw_outs_saved_for_bw:
        if ((allow_set is not None) and (saved.name not in allow_set)) or (  # type: ignore[union-attr]
            (exclude_set is not None) and (saved.name in exclude_set)  # type: ignore[union-attr]
        ):
            if isinstance(saved.meta["val"], torch.Tensor):  # type: ignore[union-attr]
                fw_outs_packed_tensors.append(saved)
            continue

        val = saved.meta["val"]  # type: ignore[union-attr]
        if not isinstance(val, torch.Tensor):
            continue

        def _get_extra_info() -> dict[str, Any]:
            return {"_fw_graph": fw_g, "_bw_graph": bw_g, "_node": saved}

        with _saved_tensor_hook_context(_get_extra_info()):
            pack_out_val = pack_hook_gm(val)

        requires_sc_handling = any(
            is_traceable_wrapper_subclass(x) for x in pytree.tree_leaves(pack_out_val)
        )
        if requires_sc_handling:
            raise NotImplementedError(
                "Tensor subclasses in GraphModule saved tensors hooks are not supported"
                "You can workaround it by manually returning subclass's inner tensors"
                " in the pack hook, and reconstructing the subclass in the unpack hook"
            )

        with _saved_tensor_hook_context(_get_extra_info()):
            pack_gm = prepare_hook_gm(aot_config, pack_hook_gm, (val,))
            pack_g = pack_gm.graph
            maybe_log_graph(
                pack_gm,
                f"saved_tensors_pack_hook {saved.name}",  # type: ignore[union-attr]
                aot_config,
                lambda: f"aot_saved_tensors_hooks_pack {saved.name}",  # type: ignore[union-attr]
                structured_logs,
            )
            pack_out_val = pack_gm(val)

        # Install pack hook graph as eiplogue of fw_module.
        # Saved tensor output becomes input of pack hook graph.
        # Replace saved tensor output with pack hook graph output.
        # Outputs symbolic scalars, tensors  are accumulated separately.
        # Then in forward outputs and backward inputs installed in order
        # sym_scalars, packed_saved_tensors.
        # Keeping all tensors together allows to preserve
        # the same identification at runtime,
        # updating only number of saved sym_scalars and tensors.
        pack_g_inputs = pack_g.find_nodes(op="placeholder")
        if len(pack_g_inputs) != 1:
            raise AssertionError(
                f"expected exactly 1 pack_g_input, got {len(pack_g_inputs)}"
            )
        env = {pack_g_inputs[0]: saved}
        fw_pack_out_args = None
        with fw_g.inserting_before(fw_out_n):
            for node in pack_g.nodes:
                if node.op == "placeholder":
                    continue
                new_n = fw_g.node_copy(node, lambda n: env[n])
                fw_g_names.add(new_n.name)
                env[node] = new_n
                # Output node is temporarily copied to have remapped arguments.
                # Removed in the end.
                if node.op == "output":
                    fw_pack_out_args = new_n.args[0]
                    fw_g.erase_node(new_n)

        env.clear()
        if not fw_pack_out_args:
            raise AssertionError("fw_pack_out_args must not be empty")
        fw_outs_bw_ins_node_names = []
        for out_idx, _n in enumerate(pytree.tree_leaves(fw_pack_out_args)):
            if not isinstance(_n, torch.fx.Node):
                fw_outs_bw_ins_node_names.append("")
                continue

            # This happens when hook is noop and it is either user input or user output.
            # Do not do anything with this node.
            if _n.op == "placeholder" or _n in fw_outs_inner_set:
                # This means the hook returned input primals unchanged
                # Do not rename in this case.
                n = _n
                new_node_name = _n.name
                fw_outs_bw_ins_node_names.append(new_node_name)
            else:
                # We can not specify desired name in node_copy.
                # Copying node manually to set specific name,
                # to have matching fw_outs, bw_inputs names.
                new_node_name = _gen_unused_name(f"{saved.name}_hook_{out_idx}")  # type: ignore[union-attr]
                with fw_g.inserting_before(_n):
                    n = fw_g.create_node(
                        _n.op,
                        _n.target,
                        _n.args,
                        _n.kwargs,
                        name=new_node_name,
                    )
                if n.name != new_node_name:
                    raise AssertionError(
                        f"expected n.name == {new_node_name}, got {n.name}"
                    )
                fw_outs_bw_ins_node_names.append(new_node_name)
                n.meta = copy.copy(_n.meta)
                _n.replace_all_uses_with(n)
                fw_g.erase_node(_n)
            if isinstance(n.meta["val"], torch.Tensor):
                fw_outs_packed_tensors.append(n)
            elif is_sym_node(n):
                fw_outs_packed_syms.append(n)

        # Install unpack hook graph as a prologue of backward graph
        # Saved tensors inputs are replaced with packed tensors and packed sym scalars.
        # The saved tensors inputs usages in the graph are replaced with unpack hook graph outputs.
        with _saved_tensor_hook_context(_get_extra_info()):
            unpack_gm = prepare_hook_gm(aot_config, unpack_hook_gm, (pack_out_val,))
            unpack_g = unpack_gm.graph
            maybe_log_graph(
                unpack_gm,
                f"saved_tensors_unpack_hook {saved.name}",  # type: ignore[union-attr]
                aot_config,
                lambda: f"aot_saved_tensors_hooks_unpack {saved.name}",  # type: ignore[union-attr]
                structured_logs,
            )

        def find_saved_in_bw_inputs(
            bw_inputs: list[torch.fx.Node],
        ) -> torch.fx.Node | None:
            for n in bw_inputs:
                if n.name == saved.name:  # type: ignore[union-attr]
                    return n

        bw_g_input = find_saved_in_bw_inputs(bw_g_inputs)
        if not bw_g_input:
            raise AssertionError(
                f"could not find saved tensor {saved.name} in bw_g_inputs"  # type: ignore[union-attr]
            )
        original_bw_g_input_users = list(bw_g_input.users.keys())
        bw_g_input_used_directly = False

        # Replace backward graph saved tensor input with copy of pack graph outputs
        # All non-Tensor, non-symscalars outputs are constanted.

        unpack_g_inputs = unpack_g.find_nodes(op="placeholder")
        env = {}
        for out_idx, (unp_in_n, out_n, val) in enumerate(
            zip(
                unpack_g_inputs,
                pytree.tree_leaves(fw_pack_out_args),
                pytree.tree_leaves(pack_out_val),
            )
        ):
            is_sym = isinstance(val, py_sym_types)
            if isinstance(val, torch.Tensor) or is_sym:
                # We want forward_outputs names to match backward_inputs,
                # Potentially backward may already have "{saved.name}_hook_{idx}",
                # In this case fx.Graph will add suffix.
                new_node_name = fw_outs_bw_ins_node_names[out_idx]
                if bw_g_input.name == new_node_name:
                    env[unp_in_n] = bw_g_input
                    bw_g_input_used_directly = True
                else:
                    # Backward calling convention: ctx_symints,ctx_saved_tensors
                    # Inserting packed sym scalars before first saved tensor input.
                    # Inserting packed tensors before last saved tensor input.
                    # Saved tensor inputs between them will be removed.
                    with (
                        bw_g.inserting_before(bw_g_inputs[0])
                        if is_sym
                        else bw_g.inserting_before(bw_g_input)
                    ):
                        new_n = bw_g.placeholder(new_node_name)
                        if new_n.name != new_node_name:
                            raise AssertionError(
                                f"expected new_n.name == {new_node_name}, got {new_n.name}"
                            )
                    new_n.meta = copy.copy(out_n.meta)
                    env[unp_in_n] = new_n
            else:
                # Inline values of non-Tensor, non-SymScalars
                env[unp_in_n] = val

        # Inserting unpack hook after placeholders.
        bw_unpack_out_n = None
        with bw_g.inserting_before(bw_g_inputs[-1].next):
            for node in unpack_g.nodes:
                if node.op == "placeholder":
                    continue
                new_n = bw_g.node_copy(node, lambda n: env[n])
                bw_g_names.add(new_n.name)
                env[node] = new_n
                # Temporary insert output, to have remapped by node_copy args.
                # Removed in the end.
                if node.op == "output":
                    bw_unpack_out_n = new_n

        if not bw_unpack_out_n:
            raise AssertionError("bw_unpack_out_n must not be None")
        _leaves = pytree.tree_leaves(bw_unpack_out_n.args)
        if len(_leaves) != 1:
            raise AssertionError(f"expected exactly 1 leaf, got {len(_leaves)}")
        unpack_saved_tensor_n = _leaves[0]

        if not bw_g_input_used_directly:
            bw_g_input.replace_all_uses_with(unpack_saved_tensor_n)
            bw_g.erase_node(bw_g_input)
        else:
            # Keep usages of bw_g_input in inserted unpacked hook graph.
            # Replace other usages of bw_g_input with unpack_saved_tensor_n.
            for use_node in original_bw_g_input_users:
                use_node._replace_input_with(bw_g_input, unpack_saved_tensor_n)
        bw_g.erase_node(bw_unpack_out_n)

    # Changing forward graph outputs,
    # Inserting packed_tensors and packed_syms on the place of saved tensors.
    # Packed sym_scalars are together with saved symints
    symint_outs_saved_for_bw = [n for n in fw_outs_saved_for_bw if is_sym_node(n)]  # type: ignore[arg-type]
    fw_new_outs = pytree.tree_leaves(
        (
            fw_outs[:num_inner_fwd_outputs],  # type: ignore[index]
            fw_outs_packed_tensors,
            fw_outs_packed_syms,
            symint_outs_saved_for_bw,
        )
    )
    fw_out_n.args = (tuple(fw_new_outs),)

    # Assert that saved tensors and symints in forward outputs are aligned with backward inputs
    _fw_n = num_inner_fwd_outputs
    _fw_num_t = len(fw_outs_packed_tensors)
    _fw_num_s = len(fw_outs_packed_syms) + len(symint_outs_saved_for_bw)
    fw_outs_saved_tensors = fw_new_outs[_fw_n : _fw_n + _fw_num_t]
    fw_outs_saved_syms = fw_new_outs[_fw_n + _fw_num_t :]
    bw_new_ins = list(bw_g.find_nodes(op="placeholder"))
    bw_ins_saved_syms = bw_new_ins[:_fw_num_s]
    bw_ins_saved_tensors = bw_new_ins[_fw_num_s : _fw_num_s + _fw_num_t]

    fw_t_names = [n.name for n in fw_outs_saved_tensors]
    bw_t_names = [n.name for n in bw_ins_saved_tensors]
    fw_s_names = [n.name for n in fw_outs_saved_syms]
    bw_s_names = [n.name for n in bw_ins_saved_syms]

    def _log_structured_logs() -> None:
        if not aot_config.enable_log:
            return

        trace_structured(
            "artifact",
            metadata_fn=lambda: {
                "name": "aot_saved_tensors_hooks_graphs",
                "encoding": "string",
            },
            payload_fn=lambda: "\n".join(structured_logs),
        )

    if aot_config.enable_log:
        structured_logs.append(
            f"fw_outs[:num_inner_fwd_outputs]:{fw_outs[:num_inner_fwd_outputs]}"  # type: ignore[index]
        )
        structured_logs.append(f"fw_outs_packed_tensors:{fw_outs_packed_tensors}")
        structured_logs.append(f"fw_t_names:{fw_t_names}")
        structured_logs.append(f"bw_t_names:{bw_t_names}")
        structured_logs.append(f"fw_s_names:{fw_s_names}")
        structured_logs.append(f"bw_s_names:{bw_s_names}")
        structured_logs.append(f"\nfw_g_pre_assert:{fw_g}")
        structured_logs.append(f"\nbw_g_pre_assert:{bw_g}")
        maybe_log_graph(
            fw_module,
            "Forward graph after transform pre-assert",
            aot_config,
            lambda: "aot_forward_graph_pre_assert_saved_tensors_hooks",
            structured_logs,
        )
        maybe_log_graph(
            bw_module,
            "Backward graph after transform pre-assert",
            aot_config,
            lambda: "aot_backward_graph_pre_assert_saved_tensors_hooks",
            structured_logs,
        )
        _log_structured_logs()

    if fw_t_names != bw_t_names:
        raise AssertionError(
            f"expected fw_t_names == bw_t_names, got {fw_t_names} != {bw_t_names}"
        )
    if fw_s_names != bw_s_names:
        raise AssertionError(
            f"expected fw_s_names == bw_s_names, got {fw_s_names} != {bw_s_names}"
        )

    fw_g.lint()
    bw_g.lint()
    fw_module.recompile()
    bw_module.recompile()
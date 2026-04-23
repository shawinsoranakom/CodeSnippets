def reinplace_inplaceable_ops_core(graph: torch.fx.Graph) -> None:
    """
    Reinplaces in-placeable operations.
    If there are no uses of a view of the mutated arg after the current node,
    it is possible to inplace the op.
    This above algorithm could be justified by observing side effects. While
    we traverse the graph in forwards direction, only latter nodes could view
    side effects of the current node. If the current node is not used later as
    well as no view of this node is used later in the graph, then it is safe to
    inplace as there would be no way to observe the side effects.
    This condition is slightly different for graph inputs where they can only
    be inplaced if the above condition is true and there's a copy_ in the
    epilogue that signals that the caller wants to observe the mutation.

    Unlike JIT Inductor, AOTInductor currently unlifts weights and buffers from
    input args, so instead of checking mutation on placeholder, AOTInductor
    checks mutation on get_attr. This is subject to change in future.
    """

    copy_args_to_copy_nodes = {}
    # maps argument to the first copy_ node that mutates it.
    copy_nodes = {}
    mutated_inputs = OrderedSet[Any]()
    storage_to_nodes = defaultdict(list)
    node_order: dict[Any, int] = {}
    for i, node in enumerate(reversed(graph.nodes)):
        node_order[node] = len(graph.nodes) - i - 1
        storage_to_nodes[get_node_storage(node)].append(node)
        if node.target is aten.copy_.default and node.args[0].op in (
            "placeholder",
            "get_attr",
        ):
            dst = node.args[0]
            src = node.args[1]
            # If the target is a getitem and it indexes a possible clone,
            # then skip over it
            if src.target is operator.getitem and (
                (
                    src.args[0].target == triton_kernel_wrapper_functional
                    and src.args[0].kwargs["kwargs"][src.args[1]] == node.args[0]
                )
                or (src.args[0].target in inplaceable_foreach_ops)
                or (src.args[0].target is torch.ops.higher_order.auto_functionalized)
            ):
                src = src.args[0]

            copy_args_to_copy_nodes[(dst, src)] = node
            copy_nodes[dst] = node

            mutated_inputs.add(node.args[0])

    def any_use_of_views_after_node(node, shared_view_nodes, *, copy_node, mutated_arg):
        node_loc = node_order[node]
        copy_node_loc = node_order[copy_node] if copy_node is not None else None

        def is_meta_only_user(node):
            if _is_view_op(node.target):
                return all(is_meta_only_user(u) for u in node.users)
            return node.target in META_ONLY_OPS

        for view in shared_view_nodes:
            for user in view.users:
                user_loc = node_order[user]
                # Skip all users before node
                if user_loc <= node_loc:
                    continue
                # Ignore uses after the copy_ epilogue node, where the input
                # has already been mutated anyway
                if copy_node_loc is not None and copy_node_loc <= user_loc:
                    continue
                # Reinplacing does not change shape metadata
                if is_meta_only_user(user):
                    continue
                # If our graph looks like:
                # foo(mutated_arg)
                # mutated_arg.copy_(other)
                # then it's safe for us to reinplace foo because mutated_arg
                # will get overwritten anyways.
                if (
                    user.target is torch.ops.aten.copy_.default
                    and mutated_arg is user.args[0]
                ):
                    continue
                return True
        return False

    def can_inplace(node, mutated_arg):
        # ls should be a list of tensors that all shares the same storage.
        def _overlap(ls) -> bool:
            try:
                return len(compute_overlapping_tensors(ls)) != 0
            except GuardOnDataDependentSymNode:
                # If we fail with data dependent error we assume they all overlap.
                return True

        if isinstance(mutated_arg, (list, tuple)):
            # TODO Using _overlap here causes a several issues.
            unique_storages = OrderedSet(get_node_storage(arg) for arg in mutated_arg)
            if len(unique_storages) != len(mutated_arg):
                # At least two Tensors in mutated_arg alias each other, so we can't reinplace it.
                # We can probably do better (that is, reinplace one of them and clone the other)
                # but that requires more work and mutable List[Tensor] are not that common.
                return False
            return all(can_inplace(node, arg) for arg in mutated_arg)

        if get_node_storage(mutated_arg) is None:
            return False

        shared_view_nodes = storage_to_nodes[get_node_storage(mutated_arg)]

        # Only keep tensor that might overlap with mutated_arg.
        shared_view_nodes = [
            v
            for v in shared_view_nodes
            if _overlap([mutated_arg.meta["val"], v.meta["val"]])
        ]

        if mutated_arg.op in ("placeholder", "get_attr"):
            # Get the first copy_ node that mutates the mutated_arg.
            copy_node = copy_nodes.get(mutated_arg)
            if copy_node is None:
                # There is no copy_ back to the candidate mutated_arg (which is a graph input).
                # Therefore the semantics of the program are that it does not mutate
                # mutated_arg, so we cannot re-inplace it.
                return False
            if any_use_of_views_after_node(
                node, shared_view_nodes, copy_node=copy_node, mutated_arg=mutated_arg
            ):
                return False

            return True
        elif any(view.op in ("placeholder", "get_attr") for view in shared_view_nodes):
            # This should never happen in auto_functionalize_v2 non-inference mode,
            # since all mutated_arg are bases.

            # If mutated arg is view of any of the inputs of the graph,
            # do not allow for inplacing.
            # This would require more sophisticated algorithm to handle
            return False
        else:
            return not any_use_of_views_after_node(
                node, shared_view_nodes, copy_node=None, mutated_arg=mutated_arg
            )

    def all_can_inplace(node, mutated_args):
        return all(can_inplace(node, arg) for arg in mutated_args)

    def log_inplace_results(
        node_name,
        old_tensors_to_clone,
        tensors_to_clone,
        missed_args,
        missed_nodes,
        trigger,
    ):
        # Total size of possibly_missed_reinplacing_opportunities for tensors with static shapes.
        missed_bytes = 0

        def bytes(node):
            t = node.meta.get("val", None)
            if (
                t is not None
                and isinstance(t.element_size(), int)
                and isinstance(t.numel(), int)
            ):
                return t.element_size() * t.numel()
            else:
                return 0

        for node in missed_nodes:
            if isinstance(node, (list, tuple)):
                for n in node:
                    missed_bytes += bytes(n)
            else:
                missed_bytes += bytes(node)

        log.info(
            "For node %s, attempted to reinplace %s. We were unable to reinplace %s; "
            "%s (if non-empty) are possible missed reinplacing opportunities that may be bad for "
            "memory usage and performance. Total size of missed opportunities with static shapes is"
            " : %s bytes.",
            node_name,
            old_tensors_to_clone,
            tensors_to_clone,
            missed_args,
            missed_bytes,
        )

        ReinplaceCounters.add_missed_opportunities(trigger, len(missed_args))
        ReinplaceCounters.add_missed_bytes(trigger, missed_bytes)

    replace_dict: dict[torch.fx.Node, torch.fx.Node] = {}

    def reinplace_and_refine_tensors_to_clone(
        old_tensors_to_clone, kwargs, node_name, trigger
    ):
        tensors_to_clone: list[str] = []
        storage_of_reinplaced_args = OrderedSet[int | None]()

        # Those used to count possibly_missed_reinplacing_opportunities
        missed_nodes = []
        missed_args = []

        # TODO this logic can be made more precise using _overlap
        def tensor_with_same_storage_already_reinplaced(arg):
            if isinstance(arg, (list, tuple)):
                return any(
                    get_node_storage(a) in storage_of_reinplaced_args for a in arg
                )
            return get_node_storage(mutated_arg) in storage_of_reinplaced_args

        for arg in old_tensors_to_clone:
            assert arg in kwargs

            mutated_arg = kwargs[arg]

            # Let's say we have:
            # - op(x, y) that mutates both x and y
            # - new_x, new_y = functional_op(x, y) is the functional variant
            # If we are presented with functional_op(x, x), we must not reinplace
            # this into op(x, x), because then it would be writing to the same Tensor.
            # Instead, it's OK to reinplace one of them and to clone the other:
            # >>> y = x.clone()
            # >>> op(x, y)
            # This also applies if we have views: functional_op(x, x[0])
            # should not reinplace into op(x, x[0]).
            should_attempt_reinplace = not tensor_with_same_storage_already_reinplaced(
                mutated_arg
            )
            if should_attempt_reinplace and can_inplace(node, mutated_arg):
                # In general, we probably do not need those optimizations.
                copy_node = copy_args_to_copy_nodes.get((mutated_arg, node))
                if copy_node is not None:
                    replace_dict[copy_node] = copy_node.args[0]
                if trigger != ReInplaceTrigger.AUTO_FUNC_V2:
                    for user in node.users:
                        # For auto_functionalize_v2, arg is the index of the base, where base at index i corresponds to
                        # output atindex size(out)+i.
                        # This used to compare string with integers before for auto_functionalize_v2. Not sure
                        # if it was needed for inplaceable_triton_ops?
                        if user.target is operator.getitem and user.args[1] == arg:
                            replace_dict[user] = mutated_arg

                if isinstance(mutated_arg, (list, tuple)):
                    for a in mutated_arg:
                        storage_of_reinplaced_args.add(get_node_storage(a))
                else:
                    storage_of_reinplaced_args.add(get_node_storage(mutated_arg))
            else:
                if should_attempt_reinplace:
                    missed_args.append(arg)
                    missed_nodes.append(mutated_arg)

                tensors_to_clone.append(arg)

        log_inplace_results(
            node_name,
            old_tensors_to_clone,
            tensors_to_clone,
            missed_args,
            missed_nodes,
            trigger,
        )
        return tensors_to_clone

    for node in graph.nodes:
        if (inplaceable_op := inplaceable_ops.get(node.target)) is not None:
            # Check if ALL mutated args can be inplaced
            # Only convert if we don't need to clone any tensor
            mutated_args = [node.args[idx] for idx in inplaceable_op.mutated_args]
            if all_can_inplace(node, mutated_args) and inplaceable_op.extra_check(node):
                for mutated_arg in mutated_args:
                    copy_node = copy_args_to_copy_nodes.get((mutated_arg, node))
                    if copy_node is not None:
                        replace_dict[copy_node] = copy_node.args[0]
                node.target = inplaceable_op.inplace_op
        elif node.target is torch.ops.higher_order.auto_functionalized_v2:
            _mutable_op = node.args[0]
            kwargs = node.kwargs

            if isinstance(
                _mutable_op, torch._ops.OpOverload
            ) and torch._library.utils.is_out(_mutable_op):
                # Out args are write-only, always safe to reinplace (no clones needed)
                node.meta["only_clone_these_tensors"] = []
            else:
                all_bases = kwargs["_all_bases"]
                bases_to_clone = range(len(all_bases))
                base_tensors_dct = dict(enumerate(all_bases))
                new_bases_to_clone: list[int] = reinplace_and_refine_tensors_to_clone(
                    bases_to_clone,
                    base_tensors_dct,
                    node.target,
                    ReInplaceTrigger.AUTO_FUNC_V2,
                )
                # Stash the metadata. There is a pass later on where we decompose
                # auto_functionalized into clones + a mutable op; this metadata
                # tells the decomp to only clone the following inputs
                node.meta["only_clone_these_tensors"] = new_bases_to_clone
        elif node.target is torch.ops.higher_order.auto_functionalized:
            _mutable_op = node.args[0]
            from torch._higher_order_ops.auto_functionalize import get_mutable_args

            tensors_to_clone, _ = get_mutable_args(_mutable_op)
            # Don't try to reinplace Tensor | None args that are None.
            tensors_to_clone = [
                t for t in tensors_to_clone if node.kwargs[t] is not None
            ]
            tensors_to_clone = reinplace_and_refine_tensors_to_clone(
                tensors_to_clone,
                node.kwargs,
                _mutable_op._name,
                ReInplaceTrigger.AUTO_FUNC_V1,
            )

            # Stash the metadata. There is a pass later on where we decompose
            # auto_functionalized into clones + a mutable op; this metadata
            # tells the decomp to only clone the following inputs
            node.meta["only_clone_these_tensors"] = tensors_to_clone
        elif node.target is torch.ops.higher_order.with_effects:
            # Handle effectful ops wrapped with with_effects
            # args[0] is the token, args[1] is the inner op, args[2:] are the op's args
            inner_op = node.args[1]
            log.debug(
                "reinplace: checking with_effects node with inner_op=%s", inner_op
            )
            if (inplaceable_op := inplaceable_ops.get(inner_op)) is not None:
                log.debug("reinplace: found inplaceable_op for %s", inner_op)
                # Get the mutated arg indices, offset by 2 (token + op)
                mutated_arg_indices = inplaceable_op.mutated_args

                # Build flat list of tensors for can_inplace check
                # and a mapping of output index -> replacement tensor(s)
                mutated_tensors_flat = []
                output_idx_to_replacement: dict[int, Any] = {}

                for position, idx in enumerate(mutated_arg_indices):
                    actual_idx = idx + 2  # offset for token and op
                    assert actual_idx < len(node.args), (
                        f"mutated arg idx {actual_idx} out of range {len(node.args)}"
                    )
                    arg = node.args[actual_idx]

                    # Output index is position + 1 (index 0 is the token)
                    output_idx = position + 1
                    output_idx_to_replacement[output_idx] = arg

                    # Flatten for can_inplace check
                    if isinstance(arg, (list, tuple)):
                        mutated_tensors_flat.extend(arg)
                    else:
                        mutated_tensors_flat.append(arg)

                # Check if all mutated args can be inplaced
                can_inplace_all = all_can_inplace(node, mutated_tensors_flat)

                log.debug(
                    "reinplace with_effects: mutated_tensors=%s, can_inplace_all=%s",
                    [str(a) for a in mutated_tensors_flat],
                    can_inplace_all,
                )

                if can_inplace_all and inplaceable_op.extra_check(node):
                    log.debug(
                        "reinplace with_effects: converting %s -> %s",
                        inner_op,
                        inplaceable_op.inplace_op,
                    )
                    # Update the inner op to inplace version
                    node.update_arg(1, inplaceable_op.inplace_op)

                    # The output structure changes: functional returns (token, tensors),
                    # inplace returns (token, None). We need to redirect tensor uses
                    # to the input tensors.

                    def get_index_from_node(n):
                        """Extract the index from a getitem node."""
                        if n.target is operator.getitem:
                            return n.args[1]
                        return None

                    def is_getitem_node(n, parent):
                        """Check if node n is a getitem indexing into parent."""
                        return n.target is operator.getitem and n.args[0] is parent

                    def replace_and_collect(current_node, replacement_tensors):
                        """
                        Collect replacements for getitem nodes into replace_dict.
                        Nodes are added in child-first order so children are erased before parents.
                        """
                        # Find all users that are getitem nodes indexing into current_node
                        getitem_users = [
                            u
                            for u in current_node.users
                            if is_getitem_node(u, current_node)
                        ]

                        if not getitem_users:
                            # Leaf node - add to replace_dict with actual replacement
                            if isinstance(replacement_tensors, (list, tuple)):
                                if len(replacement_tensors) == 1:
                                    replace_dict[current_node] = replacement_tensors[0]
                                    return True
                                else:
                                    # Multiple tensors but no indexing - can't replace
                                    return False
                            else:
                                replace_dict[current_node] = replacement_tensors
                                return True

                        # Process children first (so they're added to replace_dict before parent)
                        all_children_replaced = True
                        first_replacement = None
                        for getitem_user in getitem_users:
                            idx = get_index_from_node(getitem_user)
                            if idx is None or not isinstance(idx, int):
                                all_children_replaced = False
                                continue

                            if not isinstance(replacement_tensors, (list, tuple)):
                                all_children_replaced = False
                                continue

                            if idx >= len(replacement_tensors):
                                all_children_replaced = False
                                continue

                            if first_replacement is None:
                                first_replacement = replacement_tensors[idx]

                            if not replace_and_collect(
                                getitem_user, replacement_tensors[idx]
                            ):
                                all_children_replaced = False

                        # Add this node to replace_dict after children (even if it has non-getitem users)
                        # Non-getitem users will have their input replaced via replace_all_uses_with
                        if all_children_replaced and first_replacement is not None:
                            replace_dict[current_node] = first_replacement

                        return all_children_replaced

                    # Find getitem nodes that extract tensor results
                    # Use the output_idx_to_replacement mapping built above
                    for user in list(node.users):
                        if not is_getitem_node(user, node):
                            continue
                        idx = get_index_from_node(user)
                        if idx is None or idx not in output_idx_to_replacement:
                            continue
                        replacement = output_idx_to_replacement[idx]
                        replace_and_collect(user, replacement)
        elif node.target in inplaceable_triton_ops:
            kernel_idx = node.kwargs["kernel_idx"]
            kernel = kernel_side_table.get_kernel(kernel_idx)
            from triton.runtime.autotuner import Autotuner
            from triton.runtime.jit import JITFunction

            if isinstance(kernel, JITFunction):
                kernel_name = kernel.fn.__name__
            elif isinstance(kernel, Autotuner):
                if config.is_fbcode():
                    # Autotuner has different implementations for AMD and NV
                    if torch.version.hip is None:
                        kernel_name = kernel.base_fn.__name__
                    else:
                        kernel_name = kernel.fn.__name__
                else:
                    kernel_name = kernel.base_fn.__name__
            else:
                raise AssertionError("Unknown triton kernel type")

            # inplaceable_triton_ops take an additional argument called
            # tensors_to_clone which contain a list of tensors to clone
            # This pass iterates over them and sees which ones are safe
            # to eliminate (i.e. no longer need the clones)
            tensors_to_clone = reinplace_and_refine_tensors_to_clone(
                node.kwargs["tensors_to_clone"],
                node.kwargs["kwargs"],
                kernel_name,
                ReInplaceTrigger.TRITON_OPS,
            )

            kwargs = dict(node.kwargs)
            kwargs["tensors_to_clone"] = tensors_to_clone
            node.kwargs = immutable_dict(kwargs)
            if "eager_input_vals" in node.meta:
                # We changed the kwargs, so we need to update eager_input_vals
                # to something sane.
                args, kwargs = node.meta["eager_input_vals"]
                new_kwargs = {**kwargs}
                new_kwargs["tensors_to_clone"] = immutable_list(tensors_to_clone)
                new_kwargs = immutable_dict(new_kwargs)
                node.meta["eager_input_vals"] = (args, new_kwargs)
        elif (inplaceable_op := inplaceable_foreach_ops.get(node.target)) is not None:
            mutated_args = node.args[inplaceable_op.mutated_arg]

            if not all((arg, node) in copy_args_to_copy_nodes for arg in mutated_args):
                continue

            if can_inplace(node, mutated_args):
                for arg in mutated_args:
                    copy_node = copy_args_to_copy_nodes[(arg, node)]
                    replace_dict[copy_node] = copy_node.args[0]

                node.target = inplaceable_op.inplace_op
    for node, replacement in replace_dict.items():
        while replacement in replace_dict:
            replacement = replace_dict[replacement]
        replace_dict[node] = replacement

        node.replace_all_uses_with(replacement)
        graph.erase_node(node)
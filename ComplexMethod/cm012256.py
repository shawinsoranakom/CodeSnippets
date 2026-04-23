def constant_fold_uniform_value(gm: torch.fx.GraphModule):
    """Runs constant folding and replaces constants which can be constructed with a single `full` call. Calls into remove_no_ops."""
    with torch.utils._python_dispatch._disable_current_modes():
        aten = torch.ops.aten

        # Constant folding can leak memory, especially with repeated compilation, so we are only going to
        # remove constants which can be replaced with a constructor.
        cf = UniformValueConstantFolder(gm)
        cf.run()

        node_replacements = cf.node_replacements

        # note: [constant folding refining of symints]
        # constant folding will partially evaluate a graph such that values which have dependencies which
        # are entirely known at compile time may also become compile time constants. in some cases,
        # this will include symints which we had not yet previously deduced are guaranteed a
        # constant value and is then deduced in constant folding. an example is:
        # unbacked_symint_eq_11 = torch.full((), 11).item()
        # torch.full((unbacked_symint_eq_11,), 0)
        node_replacements_shapes = cf.node_replacements_shapes

        graph = gm.graph

        zeros = OrderedSet[Any]()
        ones = OrderedSet[Any]()

        # Got failures in `test_is_set_to_cuda` if we change aliasing on constants,
        # so just constant-ify if a Tensor is unaliased
        constant_data_ptr_count: typing.Counter[StorageWeakRef] = Counter()

        for node in cf.node_replacements:
            constant_data_ptr_count[cf.constant_data_ptrs[node]] += 1

        for node, value in node_replacements.items():
            # we dont have a functional way right now of instantiating a non-contiguous tensor with full/zeros/ones right now
            # hasn't shown up to be important yet
            if "val" not in node.meta:
                # This can only happen in AOTI
                continue

            fake_tensor = node.meta["val"]
            if not fake_tensor.is_contiguous(memory_format=torch.contiguous_format):
                continue

            # TODO - not sure about lossy uint->python value->uint conversions
            if fake_tensor.dtype in (
                torch.uint8,
                torch.uint16,
                torch.uint32,
                torch.uint64,
            ):
                continue

            if constant_data_ptr_count[cf.constant_data_ptrs[node]] > 1:
                continue

            with graph.inserting_after(node):
                # the conversion from tensor and back to value can be lossy, just use the original full ctor value
                if (
                    node.op == "call_function"
                    and node.target is aten.full.default
                    and len(node.args) == 2
                ):
                    value = node.args[1]

                # refines symints, see [constant folding refining of symints] above
                for runtime_size, compile_time_size in zip(
                    node_replacements_shapes[node], fake_tensor.shape
                ):
                    torch._check(runtime_size == compile_time_size)

                # replace SymInt as Node before creating a new full node
                # e.g. (1, s0) -> (1, arg0_1)
                node_shape = node_replacements_shapes[node]
                if not all(
                    not isinstance(s, torch.SymInt) or s in cf.symint_nodes
                    for s in node_shape
                ):
                    continue

                shapes = [
                    cf.symint_nodes[s] if isinstance(s, torch.SymInt) else s
                    for s in node_replacements_shapes[node]
                ]

                # Check if any shape depends on a symint that was computed from
                # the node being replaced - this would create a cycle
                if _has_self_referential_shape(shapes, node):
                    continue

                # zeros and ones just get traced into full, so we insert those
                new_node = graph.call_function(
                    aten.full.default,
                    args=(shapes, value),
                    kwargs={
                        "dtype": fake_tensor.dtype,
                        "layout": torch.strided,
                        "device": fake_tensor.device,
                        "pin_memory": node.kwargs.get("pin_memory", False),
                    },
                )

                new_node.meta.update(node.meta)
                node.replace_all_uses_with(new_node)
                graph.erase_node(node)

                if value == 0:
                    zeros.add(new_node)
                elif value == 1:
                    ones.add(new_node)

        remove_no_ops(gm, zeros, ones)
        remove_redundant_views(gm)
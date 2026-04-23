def run_joint_graph_passes_on_hops(
    joint_gm: torch.fx.GraphModule,
    joint_inputs: Any,
    aot_config: AOTConfig,
) -> torch.fx.GraphModule:
    """
    This pass runs the joint graph passes on the HOP graph. In torch.compile, we
    typically have many passes which work on the joint graph and then end with a
    partitioner.


    The partitioner part is quite mechanical to handle. HOP have their own
    forward and backward graph. The process can be broken into following steps

    1) Get a `joint_hop_gm` from the `fw_hop_gm` and `bw_hop_gm`
    2) Run joint graph passes on the `joint_hop_gm` to get `new_fw_hop_gm` and `new_bw_hop_gm`
    3) Stitch the `new_fw_hop_gm` and `new_bw_hop_gm` back into the `joint_gm`.

    The terminology used in the code is
    `joint_graph/joint_gm` : Refers to the main graph. This may contain many HOPs which have their own `hop_graph`
    `fw_hop_graph/fw_hop_gm` : Refers to the forward graph associated with a HOP.
    `bw_hop_graph/bw_hop_gm` : Refers to the backward graph associated with a HOP.
    `joint_hop_graph/joint_hop_gm` : Refers to the subgraph associated with the HOP like invoke_subgraph.
    `new_fw_hop_graph/new_fw_hop_gm` : Refers to the forward graph after partitioning is applied to `joint_hop_gm`.
    `new_bw_hop_graph/new_bw_hop_gm` : Refers to the backward graph after partitioning is applied to `joint_hop_gm`.

    NB: This pass works for invoke_subgraph today because we took extra care in
    the Autograd.Dispatch key of invoke_subgraph to vastly simplify Step 1.
    """
    from torch._higher_order_ops import invoke_subgraph

    def num_outputs(mod: torch.fx.GraphModule) -> int:
        return len(mod.graph.find_nodes(op="output")[0].args[0])

    def num_inputs(mod: torch.fx.GraphModule) -> int:
        return len(mod.graph.find_nodes(op="placeholder"))

    new_hop_graphs: dict[str, InvokeSubgraphHopGraphs] = defaultdict(
        lambda: InvokeSubgraphHopGraphs()
    )

    # Step 1 - Get a `joint_hop_gm` from the `fw_hop_gm` and `bw_hop_gm` This is
    # easy to do for `invoke_subgraph` HOP. During the Autograd dispatch key
    # tracing, we have put the joint_hop_graph in the backward hop graph itself.
    # So to recover the joint_hop_gm, we just have to look at the backward
    # HOP graphs.
    # So we will merge step 1 and step 2 in this next section

    # Save the fw and bwd hop nodes. We will later in-place modify the graph
    # using these nodes.
    # pyrefly: ignore [implicit-any]
    fw_hop_nodes = []
    # pyrefly: ignore [implicit-any]
    bw_hop_nodes = []
    for node in joint_gm.graph.nodes:
        if (
            node.op == "call_function"
            and node.target is invoke_subgraph
            and isinstance(node.args[1], str)
        ):
            if node.args[1].startswith("fw"):
                fw_hop_nodes.append(node)
            elif node.args[1].startswith("bw"):
                bw_hop_nodes.append(node)

    if not bw_hop_nodes:
        return joint_gm

    if len(fw_hop_nodes) != len(bw_hop_nodes):
        raise AssertionError(
            f"expected len(fw_hop_nodes) == len(bw_hop_nodes), "
            f"got {len(fw_hop_nodes)} != {len(bw_hop_nodes)}"
        )

    # Create a bw to hop node mapping. This helps us in identifying the bw and
    # fw subgraph pairs without relying on the identifier. This is important
    # because we can have different subgraphs for bwd for same subgraph in the
    # fwd because of differing strides in the backward.
    bw_to_fw_hop_node = dict(zip(list(reversed(bw_hop_nodes)), fw_hop_nodes))

    for node in bw_hop_nodes:
        identifier = node.args[1].removeprefix("bw")

        # If partitioning already done for this identifier, skip. This saves
        # redundant joint graph passes for same subgraphs.
        if new_hop_graphs[identifier].partitioning_done:
            continue

        # Collect some information from the forward hop graph
        fw_hop_node = bw_to_fw_hop_node[node]
        fw_hop_gm = getattr(joint_gm, fw_hop_node.args[0].target)
        if not isinstance(fw_hop_gm, torch.fx.GraphModule):
            raise AssertionError(
                f"expected fw_hop_gm to be GraphModule, got {type(fw_hop_gm)}"
            )
        num_fw_inputs = num_inputs(fw_hop_gm)
        num_fw_outputs = num_outputs(fw_hop_gm)
        new_hop_graphs[identifier].old_num_fw_inputs = num_fw_inputs
        new_hop_graphs[identifier].old_num_fw_outputs = num_fw_outputs

        # Step 1) - Get the `joint_hop_gm`. As mentioned earlier, the
        # backward graph is the joint graph.
        joint_hop_gm = getattr(joint_gm, node.args[0].target)
        if not isinstance(joint_hop_gm, torch.fx.GraphModule):
            raise AssertionError(
                f"expected joint_hop_gm to be GraphModule, got {type(joint_hop_gm)}"
            )

        # Prepare the graph for the partitioner
        joint_hop_gm = prepare_for_partitioner(
            joint_hop_gm, num_fw_inputs, num_fw_outputs
        )

        # TODO: invoke_subgraph should track which of its inputs static indices
        # so it can propagate them to the partitioner (and use in cudagraphs)
        static_lifetime_input_indices: list[int] = []

        used_hop_custom_partition, partition_fn = _get_partition_fn(
            fw_hop_node, aot_config
        )

        # Step 2) and 3) - Run joint graph passes and partitioner
        try:
            new_fw_hop_gm, new_bw_hop_gm = partition_fn(
                joint_hop_gm,
                [],
                num_fwd_outputs=num_fw_outputs,
                static_lifetime_input_indices=static_lifetime_input_indices,
            )
        except Exception as e:
            if used_hop_custom_partition:
                raise RuntimeError(
                    f"Error in custom partition function for invoke_subgraph node {fw_hop_node.name}: {e}"
                ) from e
            else:
                raise

        # Save the new forward and backward graph modules
        new_hop_graphs[identifier].new_fw_hop_gm = new_fw_hop_gm
        new_hop_graphs[identifier].new_bw_hop_gm = new_bw_hop_gm

        # Save the number of symints and saved tensors
        new_fw_out_nodes = new_fw_hop_gm.graph.find_nodes(op="output")[0].args[0]
        extra_outputs = new_fw_out_nodes[num_fw_outputs:]
        symint_outputs = [n for n in extra_outputs if is_sym_node(n)]

        new_hop_graphs[identifier].new_num_sym_nodes = len(symint_outputs)
        new_hop_graphs[identifier].new_num_saved_nodes = len(extra_outputs) - len(
            symint_outputs
        )

        new_hop_graphs[identifier].partitioning_done = True

    # Step 3) Restitch the new fw and bw graphs back into the main graph.
    #
    # This is a very mechanical process. There are a quite a few pieces that we
    # need to connect together to make it work. Lets try to understand the
    # problem statement first.
    #
    # For the forward graph, the signature of the old_fw_hop_gm is
    #   inputs - (*primals)
    #   outputs - (*fw_outs)
    # Now the signature of the new_fw_hop_gm is
    #   inputs - (*primals)     -- This is same
    #   outputs - (*fw_outs, *saved_tensors)    - This is different
    # At a high level, this is an easy transformation, in the new graph we just
    # have to replace the old_fw_hop_gm with the new_fw_hop_gm. Everything else
    # falls into place, because the input signature (i.e. args) is same. And
    # even though output signature is different, fw_outs are still at the same
    # indexes as before. So the forward of the `joint_gm` works nicely.
    #
    # Now, lets look at the backward hop graph. Old signature
    #   inputs - (*primals, *tangents)
    #   outputs - (*grad_outs, *fw_outs)
    # New signature
    #   inputs - (*saved_tensors, *tangents) -- Different
    #   outputs - (*grad_outs)  -- Different
    # Here both input and output signature change. The output signature handling
    # is quite easy because the grads_out are sitting at the right place, so we
    # dont have to do anything.
    #
    # For the input signature, we have to collect the saved tensors from the
    # corresponding forward graph output. We collect all saved_tensors when we
    # see the forward graph, and save it into a map and then later use it during
    # the backward.

    # The stack of fw_nodes for invoke_subgraph HOP. There is an implicit
    # assumption about the graph structure, i.e., if we have hop1, hop2, hop3,
    # ... in the forward part of the joint graph, we will have .., hop3, hop2,
    # hop1 order for the backward. This structure allows us to just use a stack
    # to collect all the information that we need to pass from the forward hop
    # node to the corresponding backward node.

    already_added_new_hop_mods = set()

    def add_new_hop_gm(new_subgraph_mod: torch.fx.GraphModule, name: str) -> str:
        new_subgraph_attr_name = f"partitioned_{name}"
        if new_subgraph_attr_name in already_added_new_hop_mods:
            return new_subgraph_attr_name

        joint_gm.register_module(new_subgraph_attr_name, new_subgraph_mod)
        already_added_new_hop_mods.add(new_subgraph_attr_name)
        return new_subgraph_attr_name

    def propagate_meta_info(
        new_hop_gm: torch.fx.GraphModule,
        new_call_function_node: torch.fx.Node,
        old_call_function_node: torch.fx.Node,
    ) -> None:
        # Copy all the fields from the old call_function node. And then override
        # the `val` meta field with the outputs of new_hop_gm.
        new_call_function_node.meta = copy.copy(old_call_function_node.meta)

        output = new_hop_gm.graph.find_nodes(op="output")[0]
        out_example_vals = [n.meta["val"] if n else None for n in output.args[0]]
        new_call_function_node.meta["val"] = tuple(out_example_vals)

    for bw_node in reversed(bw_hop_nodes):
        identifier = bw_node.args[1].removeprefix("bw")

        # Make changes to the corresponding fw and bw node pair simultaneously.
        # The removes the need of any bookkeeping.

        # Fw node changes
        # Insert the new_fw_hop_gm. This is straightforward. Get the
        # new_fw_hop_gm, insert the hop_gm as a get_attr fw_node, and then
        # add a call_function fw_node. Additionally, also use getitem
        # call_functions to collect the saved_tensor nodes

        fw_node = bw_to_fw_hop_node[bw_node]
        new_fw_hop_gm = new_hop_graphs[identifier].new_fw_hop_gm
        if new_fw_hop_gm is None:
            raise AssertionError(
                f"new_fw_hop_gm for identifier {identifier} must not be None"
            )

        old_num_fw_outputs = new_hop_graphs[identifier].old_num_fw_outputs
        new_num_sym_nodes = new_hop_graphs[identifier].new_num_sym_nodes
        new_num_saved_nodes = new_hop_graphs[identifier].new_num_saved_nodes
        if old_num_fw_outputs is None:
            raise AssertionError(
                f"old_num_fw_outputs for identifier {identifier} must not be None"
            )
        if new_num_sym_nodes is None:
            raise AssertionError(
                f"new_num_sym_nodes for identifier {identifier} must not be None"
            )
        if new_num_saved_nodes is None:
            raise AssertionError(
                f"new_num_saved_nodes for identifier {identifier} must not be None"
            )
        total_outputs = old_num_fw_outputs + new_num_saved_nodes + new_num_sym_nodes

        extra_fw_outputs = []

        # Insert the new_fw_hop_gm into the joint_gm
        with joint_gm.graph.inserting_after(fw_node):
            new_fw_mod_attr_name = add_new_hop_gm(new_fw_hop_gm, f"fw{identifier}")
            new_fw_mod_attr = joint_gm.graph.get_attr(new_fw_mod_attr_name)
            new_fw_mod_attr.meta = copy.copy(fw_node.args[0].meta)

        # new_hop_fw_gm output signature is (*fw_outs, *saved_tensors)
        with joint_gm.graph.inserting_after(new_fw_mod_attr):
            new_fw_node = joint_gm.graph.call_function(
                the_function=invoke_subgraph,
                args=(
                    new_fw_mod_attr,
                    new_fw_mod_attr_name,
                    *fw_node.args[2:],
                ),
            )
            propagate_meta_info(new_fw_hop_gm, new_fw_node, fw_node)

        # old_num_fw_outputs = (*fw_outs)
        # new_num_fw_outputs = (*fw_outs, *saved_tensors, *sym_nodes)
        with joint_gm.graph.inserting_after(new_fw_node):
            for fw_out_idx in range(old_num_fw_outputs, total_outputs):
                saved_tensor_node = joint_gm.graph.call_function(
                    the_function=operator.getitem, args=(new_fw_node, fw_out_idx)
                )
                saved_tensor_node.meta = copy.copy(new_fw_node.meta)
                saved_tensor_node.meta["val"] = new_fw_node.meta["val"][fw_out_idx]
                extra_fw_outputs.append(saved_tensor_node)

        fw_node.replace_all_uses_with(new_fw_node)
        joint_gm.graph.erase_node(fw_node)

        # Bw node changes
        # Prepare the operands for the bwd graph
        # Old bw graph signature : (*primals, *tangents)
        # New signature will be : (*sym_nodes, *saved_tensors, *tangents)
        # We have already collected the saved_tensors in the forward hop processing.

        # extra_fw_outputs are in the order (*saved_nodes, *sym_nodes).
        # Partitioner has this quirk where the backward wants sym_nodes
        # first. So extract the sym and saved nodes.

        new_bw_hop_gm = new_hop_graphs[identifier].new_bw_hop_gm
        if new_bw_hop_gm is None:
            raise AssertionError(
                f"new_bw_hop_gm for identifier {identifier} must not be None"
            )

        saved_tensor_nodes = extra_fw_outputs[:new_num_saved_nodes]
        sym_nodes = extra_fw_outputs[new_num_saved_nodes:]

        num_primals = new_hop_graphs[identifier].old_num_fw_inputs
        if num_primals is None:
            raise AssertionError(
                f"num_primals for identifier {identifier} must not be None"
            )
        tangents = list(bw_node.args[2 + num_primals :])
        operands = sym_nodes + saved_tensor_nodes + tangents

        # Insert the new_bw_hop_gm into the joint_gm
        with joint_gm.graph.inserting_after(bw_node):
            new_bw_mod_attr_name = add_new_hop_gm(new_bw_hop_gm, bw_node.args[1])
            new_bw_mod_attr = joint_gm.graph.get_attr(new_bw_mod_attr_name)
            new_bw_mod_attr.meta = copy.copy(bw_node.args[0].meta)

        with joint_gm.graph.inserting_after(new_bw_mod_attr):
            new_bw_node = joint_gm.graph.call_function(
                the_function=invoke_subgraph,
                args=(
                    new_bw_mod_attr,
                    new_bw_mod_attr_name,
                    *operands,
                ),
            )
            propagate_meta_info(new_bw_hop_gm, new_bw_node, bw_node)
            # Since the partitioner is run after the graph passes, we have lost
            # the eager information and cannot faithfully extract the eager
            # inputs for the new partitioned backward graph. For the forward
            # graph, it was fine because the input signature remains same.
            new_bw_node.meta.pop("eager_input_vals", None)

        bw_node.replace_all_uses_with(new_bw_node)
        joint_gm.graph.erase_node(bw_node)

    joint_gm.graph.eliminate_dead_code()
    joint_gm.graph.lint()
    joint_gm.recompile()
    return joint_gm
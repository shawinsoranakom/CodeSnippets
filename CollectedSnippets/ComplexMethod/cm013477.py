def optimize_for_inference(
    model: torch.nn.Module,
    pass_config: dict[str, Any] | None = None,
    tracer: type[fx.Tracer] = fx.Tracer,
) -> torch.nn.Module:
    """
    Performs a set of optimization passes to optimize a model for the
    purposes of inference. Specifically, the passes that are run are:
    1. Conv/BN fusion
    2. Dropout removal
    3. MKL layout optimizations

    The third optimization takes a function `use_mkl_heuristic` that's used
    to determine whether a subgraph should be explicitly run in MKL layout.

    Note: As FX does not currently handle aliasing, this pass currently
    assumes nothing aliases. If that isn't true, use at your own risk.
    """
    default_pass_config = {
        "conv_bn_fuse": True,
        "remove_dropout": True,
        "mkldnn_layout_optimize": {"heuristic": use_mkl_length},
    }
    if pass_config is None:
        pass_config = {}
    default_pass_config.update(pass_config)

    if default_pass_config["conv_bn_fuse"]:
        model = fuse(model)
    if default_pass_config["remove_dropout"]:
        model = remove_dropout(model)
    if default_pass_config["mkldnn_layout_optimize"] is False:
        return model
    if not isinstance(default_pass_config["mkldnn_layout_optimize"], dict):
        raise RuntimeError("mkldnn_layout_optimize config is not a dict")
    if "heuristic" not in default_pass_config["mkldnn_layout_optimize"]:
        raise RuntimeError("Heuristic not found in mkldnn_layout_optimize config")
    use_mkl_heuristic = default_pass_config["mkldnn_layout_optimize"]["heuristic"]

    cur_tracer = tracer()
    fx_graph = cur_tracer.trace(copy.deepcopy(model))
    fx.GraphModule(cur_tracer.root, fx_graph)
    modules: dict[str, nn.Module] = dict(model.named_modules())

    class MklSupport(Enum):
        NO = 1
        YES = 2
        UNKNOWN = 3

    # Inserts to_mkldnn and to_dense around every node we want to be a MKLDNN node.
    # If the op is in `mkldnn_supported` then we always treat it as a MKLDNN node.
    # However, if it's in `mkldnn_supported_unknown`, then we only treat it as
    # a MKLDNN node if its inputs are MKLDNN nodes.
    for node in list(fx_graph.nodes):
        supports_mkldnn = MklSupport.NO
        if node.op == "call_module":
            cur_module = modules[node.target]
            if type(cur_module) in mkldnn_supported:
                supports_mkldnn = MklSupport.YES
                sample_parameter = next(cur_module.parameters(), None)
                if sample_parameter is not None:
                    if sample_parameter.dtype != torch.float:
                        raise AssertionError(
                            "this pass is only for torch.float modules"
                        )
                    if sample_parameter.device != torch.device("cpu"):
                        raise AssertionError("this pass is only for CPU modules")
        elif node.op == "call_function":
            if node.target in mkldnn_supported:
                supports_mkldnn = MklSupport.YES
            elif node.target in mkldnn_supported_unknown:
                supports_mkldnn = MklSupport.UNKNOWN

        if supports_mkldnn != MklSupport.NO:
            if supports_mkldnn == MklSupport.UNKNOWN:
                if not any(arg.target == "to_dense" for arg in node.args):
                    continue
            with fx_graph.inserting_before(node):
                mkldnn_args = fx.map_arg(
                    node.args, lambda n: fx_graph.call_method("to_mkldnn", (n,))
                )

            node.args = cast(tuple[fx.node.Argument], mkldnn_args)

            with fx_graph.inserting_after(node):
                dense_x = fx_graph.create_node("call_method", "to_dense", (node,))
                node.replace_all_uses_with(dense_x)
                dense_x.args = (node,)

    # Does pre-conversion of all modules into MKLDNN (when possible)
    old_modules = modules_to_mkldnn(list(fx_graph.nodes), modules)
    fx_graph.old_modules = old_modules  # type: ignore[attr-defined]

    # optimizes all a -> to_dense -> to_mkldnn -> b patterns into a -> b
    for node in fx_graph.nodes:
        if node.op == "call_method" and node.target == "to_dense":
            prv_node = node.args[0]
            users = list(node.users)
            for user in users:
                if user.op == "call_method" and user.target == "to_mkldnn":
                    user.replace_all_uses_with(prv_node)
                    fx_graph.erase_node(user)
            if len(node.users) == 0:
                fx_graph.erase_node(node)

    num_nodes = len(fx_graph.nodes)
    uf = UnionFind(num_nodes)

    def get_color(n: fx.Node) -> int | None:
        if hasattr(n, "color"):  # Current node is part of a MKL subgraph
            return uf.find(n.color)
        if hasattr(n, "start_color"):  # Current node is input to MKL subgraph
            return uf.find(n.start_color)
        return None

    # This code is to find each MKLDNN subgraph. Each MKLDNN subgraph consists
    # of input nodes (which are only `to_mkldnn` calls), output nodes
    # (`to_dense` calls), and intermediate nodes, which are run entirely on
    # MKLDNN layout tensors.
    #
    # Specifically, this code does a flood fill on a directed acyclic graph
    # (DAG), starting from each possible "start node" (i.e: `to_mkldnn` nodes).
    # If every node only had one input, this would be sufficient. However, in
    # the case that a node has multiple inputs coming from different start
    # nodes (i.e. colors), we need to join these 2 colors into 1. That's done
    # using a Disjoint Set Union.
    for cur_idx, node in enumerate(fx_graph.nodes):
        if node.op == "call_method" and node.target == "to_mkldnn":
            node.start_color = cur_idx
            uf.make_set(cur_idx)
        elif node.op == "call_method" and node.target == "to_dense":
            if get_color(node.args[0]) is None:
                raise AssertionError("Expected color for to_dense input")
            node.end_color = get_color(node.args[0])
        else:
            cur_colors = [
                get_color(i)
                for i in node.all_input_nodes
                if isinstance(i, fx.Node)
                if get_color(i) is not None
            ]

            if len(cur_colors) == 0:
                continue
            if any(i is None for i in cur_colors):
                raise AssertionError("Found None in cur_colors")
            sorted_colors: list[int] = sorted(cur_colors)  # type: ignore[arg-type]
            node.color = sorted_colors[0]
            for other_color in sorted_colors[1:]:
                uf.join(sorted_colors[0], other_color)

    mkldnn_graphs: dict[int, MklSubgraph] = defaultdict(lambda: MklSubgraph(fx_graph))
    for node in fx_graph.nodes:
        if hasattr(node, "color"):
            mkldnn_graphs[uf.find(node.color)].nodes.append(node)
        if hasattr(node, "start_color"):
            mkldnn_graphs[uf.find(node.start_color)].start_nodes.append(node)
        if hasattr(node, "end_color"):
            mkldnn_graphs[uf.find(node.end_color)].end_nodes.append(node)

    # Now that we have all the subgraphs, we need to decide which MKLDNN
    # subgraphs we actually want to keep in MKLDNN.
    for graph in mkldnn_graphs.values():
        if not use_mkl_heuristic(graph):
            for node in graph.start_nodes + graph.end_nodes:
                prv = node.args[0]
                node.replace_all_uses_with(prv)  # type: ignore[arg-type]
                fx_graph.erase_node(node)
            reset_modules(graph.nodes, modules, old_modules)

    mkldnn_conversions = 0
    for node in fx_graph.nodes:
        if node.target == "to_mkldnn" or node.target == "to_dense":
            mkldnn_conversions += 1

    logging.getLogger(__name__).info("mkldnn conversions: %s", mkldnn_conversions)
    fx_graph.lint()
    result = fx.GraphModule(model, fx_graph)
    return result
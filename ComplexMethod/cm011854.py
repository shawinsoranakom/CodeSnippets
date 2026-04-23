def create_fx_from_snodes(snodes: list[BaseSchedulerNode]) -> fx.Graph:
    """
    Creates a FX Graph from a list of SchedulerNode objects.
    """

    def get_fake_func(name: str) -> Callable[..., int]:
        def func1(*args: Any) -> int:
            return 0

        func1.__name__ = name
        return func1

    FusionMeta = collections.namedtuple("FusionMeta", ["group", "snode", "type"])

    buf_to_fx_node = {}
    node_to_fx_node = {}
    graph = torch.fx.Graph()
    first_node = None

    outputs = []
    group: Any = None
    # create call_function node for each Buffer and Kernel
    # pyrefly: ignore [bad-assignment]
    for snode in snodes:
        if snode.is_extern():
            node_type = "extern"
            group = node_type
        elif snode.is_template():
            node_type = "template"
            group = node_type
        elif isinstance(snode, NopKernelSchedulerNode):
            node_type = "nop"
            group = node_type
        elif isinstance(snode, SchedulerNode):
            node_type = "compute"
            group = snode.group
        elif isinstance(snode, FusedSchedulerNode):
            node_type = "fused"
            group = snode.group
        else:
            raise RuntimeError("Unknown node type")

        fused_name = torch._inductor.utils.get_fused_kernel_name(
            snode.get_nodes(), "original_aten"
        )
        func_name = f"{node_type}: {fused_name}"
        node_func = get_fake_func(func_name)
        kwargs = {}
        if hasattr(snode, "get_device"):
            kwargs = {"device": snode.get_device()}
        fx_node = graph.call_function(node_func, args=(), kwargs=kwargs)  # type: ignore[arg-type]

        def in_output(snode: BaseSchedulerNode | FusedSchedulerNode) -> bool:
            if isinstance(snode, FusedSchedulerNode):
                return any(in_output(x) for x in snode.snodes)
            return any(
                isinstance(user.node, OutputNode)
                for buf in snode.get_outputs()
                for user in buf.users
            )

        if in_output(snode):
            outputs.append(fx_node)
        name = snode.get_name()
        fx_node.name = name

        fx_node.meta["fusion_meta"] = FusionMeta(group, snode, node_type)

        node_to_fx_node[name] = fx_node
        for buf in snode.get_outputs():
            buf_to_fx_node[buf.get_name()] = fx_node

        if first_node is None:
            first_node = fx_node

    # create edges between nodes
    for snode in snodes:
        name = snode.get_name()
        deps = snode.read_writes.reads

        fx_node = node_to_fx_node[name]
        new_args = []
        for dep in deps:
            if dep.name in buf_to_fx_node:
                dep_node = buf_to_fx_node[dep.name]
            else:
                with graph.inserting_before(first_node):
                    dep_node = graph.placeholder(dep.name)
                    buf_to_fx_node[dep.name] = dep_node
            if dep_node == fx_node:  # to avoid cycles
                continue
            new_args.append(dep_node)

        fx_node.args = tuple(new_args)

    graph.output(outputs[0] if len(outputs) == 1 else tuple(outputs))
    return graph
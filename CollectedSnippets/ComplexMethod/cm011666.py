def dump_node_schedule(node_schedule: Sequence[BaseSchedulerNode]) -> None:
    """
    An API that can be used in pdb to dump a node_schedule.
    Right mainly dump the read/write dependencies but can add more as needed.
    """
    from torch._inductor.codegen.simd import DisableReduction, EnableReduction
    from torch._inductor.scheduler import SchedulerNode

    print(f"Node schedule with {len(node_schedule)} nodes")
    for idx, node in enumerate(node_schedule):
        print(f" {idx:3}:")
        # pyrefly: ignore [unnecessary-comparison]
        if node is EnableReduction:
            print("enable reduction")
        # pyrefly: ignore [unnecessary-comparison]
        elif node is DisableReduction:
            print("disable reduction")
        elif isinstance(node, SchedulerNode):
            is_red = node.is_reduction()
            print(f"{'red' if is_red else 'pw'} scheduler node")
            if is_red:
                assert node.node is not None
                print(f"original reduction hint {node.node.data.reduction_hint}")  # type: ignore[attr-defined]
            print("ReadDep:")
            for dep in node.read_writes.reads:
                print(dep)
            print("WriteDep:")
            for dep in node.read_writes.writes:
                print(dep)
        else:
            raise RuntimeError(f"Unrecognized node type: {type(node)}")
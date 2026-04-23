def export_graph_for_simulator(
    nodes: list[BaseSchedulerNode],
    name_to_freeable_input_buf: dict[str, FreeableInputBuffer],
    name_to_fused_node: dict[str, BaseSchedulerNode],
    graph_inputs: OrderedSet[str],
    graph_outputs: OrderedSet[str],
) -> None:
    """
    This is for debugging purposes. It will dump a json file that records graph information.
    The graph can then be used in a simulator: https://fburl.com/code/3l3d3qi4
    """

    class ORMBuffer(TypedDict):
        name: str
        size_alloc: int
        size_free: int
        size: int  # for backward compatibility
        is_input: bool
        is_output: bool
        deps: list[str]
        unmet_deps: list[str]

    class ORMNode(TypedDict):
        name: str
        buffer_names: list[str]

    class ORMGraph(TypedDict):
        nodes: list[ORMNode]
        buffers: list[ORMBuffer]

    orm_buffers: list[ORMBuffer] = []
    orm_nodes: list[ORMNode] = []

    # get orm buffers for freeable input buffers
    for buf_name, input_buf in name_to_freeable_input_buf.items():
        orm_buf_input_buffer: ORMBuffer = {
            "name": buf_name,
            "size_alloc": input_buf.mpi_buffer.size_free,
            "size_free": input_buf.mpi_buffer.size_free,
            "size": input_buf.mpi_buffer.size_free,
            "is_input": True,
            "is_output": buf_name in graph_outputs,
            "deps": [],
            "unmet_deps": [],
        }
        orm_buffers.append(orm_buf_input_buffer)

    # get orm buffers for scheduler buffers
    name_to_buf: dict[str, SchedulerBuffer] = {
        buf.get_name(): buf for node in nodes for buf in node.get_outputs()
    }  # need to reassign due to probably node pruning
    for buf_name, sched_buf in name_to_buf.items():
        if sched_buf.defining_op is None:
            continue
        deps = [
            pred_buf.get_name()
            for pred_buf in name_to_fused_node[
                sched_buf.defining_op.get_name()
            ].mpi_node.pred_buffers
        ]
        orm_buf_scheduler_buffer: ORMBuffer = {
            "name": buf_name,
            "size_alloc": sched_buf.mpi_buffer.size_alloc,
            "size_free": sched_buf.mpi_buffer.size_free,
            "size": sched_buf.mpi_buffer.size_free,
            "is_input": False,
            "is_output": buf_name in graph_outputs,
            "deps": deps,
            "unmet_deps": [
                buf_name for buf_name in deps if buf_name not in graph_inputs
            ],
        }
        orm_buffers.append(orm_buf_scheduler_buffer)

    # get orm nodes
    for node in nodes:
        orm_node: ORMNode = {
            "name": node.get_name(),
            "buffer_names": list(node.get_buffer_names()),
        }
        orm_nodes.append(orm_node)

    # create the graph object
    g: ORMGraph = {
        "nodes": orm_nodes,
        "buffers": orm_buffers,
    }

    # dump the graph
    import json
    import os

    import torch
    from functorch.compile import get_graph_being_compiled

    name = os.path.splitext(get_graph_being_compiled())[0] + "_fused"

    g_str = json.dumps(g, indent=2)

    torch._logging.trace_structured(
        "artifact",
        metadata_fn=lambda: {
            "name": name,
            "encoding": "string",
        },
        payload_fn=lambda: g_str,
    )
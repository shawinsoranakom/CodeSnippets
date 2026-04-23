def compute_memory_timeline(
    nodes: list[BaseSchedulerNode],
    name_to_freeable_input_buf: dict[str, FreeableInputBuffer],
    graph_outputs: OrderedSet[str],
) -> tuple[
    list[BufferInfo],
    dict[BaseSchedulerNode, int],
    dict[FreeableInputBuffer | SchedulerBuffer, BaseSchedulerNode],
]:
    """
    Compute buffer allocation and deallocation sizes and map their
    lifetime to the node schedule
    """

    # get the execution step of each node, this will be used to determine
    # the end_step of buffers
    node_to_step: dict[BaseSchedulerNode, int] = {
        node: step for step, node in enumerate(nodes)
    }

    # get buffers' size and liveliness information
    buf_info_list: list[BufferInfo] = []
    buf_to_snode_last_use: dict[
        FreeableInputBuffer | SchedulerBuffer, BaseSchedulerNode
    ] = {}

    def _get_end_step_and_snode(
        buf: FreeableInputBuffer | SchedulerBuffer,
    ) -> tuple[int, BaseSchedulerNode | None]:
        max_step: int = -1
        max_step_snode: BaseSchedulerNode | None = None
        succ_nodes = buf.mpi_buffer.succ_nodes
        if succ_nodes:
            for succ_node in succ_nodes:
                step = node_to_step[succ_node]
                if step > max_step:
                    max_step = step
                    max_step_snode = succ_node
            assert max_step_snode is not None
        return max_step, max_step_snode

    # 1. for freeable input buffers
    for buf_name, input_buf in name_to_freeable_input_buf.items():
        end_step = -1
        if buf_name not in graph_outputs:
            end_step, end_step_snode = _get_end_step_and_snode(input_buf)
            assert end_step_snode is not None
            buf_to_snode_last_use[input_buf] = end_step_snode

        buf_info_list.append(
            BufferInfo(
                input_buf,
                input_buf.mpi_buffer.size_free,
                input_buf.mpi_buffer.size_free,
                0,
                end_step,
            )
        )

    # 2. for scheduler buffers
    for step, node in enumerate(nodes):
        for sched_buf in node.get_outputs():
            # note: it is possible for a non-graph-output sched_buf to have no succ_nodes and
            # to be only used by its defining op (e.g., due to fusion when all consumers of
            # the buffer are fused with its defining op). In such cases, end_step is step.
            buf_name = sched_buf.get_name()
            end_step = -1
            if buf_name not in graph_outputs:
                end_step, end_step_snode = _get_end_step_and_snode(sched_buf)
                if end_step == -1:
                    end_step = step
                    buf_to_snode_last_use[sched_buf] = node
                else:
                    assert end_step_snode is not None
                    buf_to_snode_last_use[sched_buf] = end_step_snode

            buf_info_list.append(
                BufferInfo(
                    sched_buf,
                    sched_buf.mpi_buffer.size_alloc,
                    sched_buf.mpi_buffer.size_free,
                    step,
                    end_step,
                )
            )

    return buf_info_list, node_to_step, buf_to_snode_last_use
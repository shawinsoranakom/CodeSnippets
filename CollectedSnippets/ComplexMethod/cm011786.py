def topological_sort_bfs(nodes: list[BaseSchedulerNode]) -> list[BaseSchedulerNode]:
    """
    A BFS topological sort that selects nodes whose dependencies are executed the
    earliest. This follows a FIFO idea. Specifically, at every iteration, for each node
    that is schedulable, we gather the order in which its predecessor nodes are executed,
    and this sorted list of execution orders of predecessor nodes defines the priority.
    We select the node whose predecessors nodes are executed the earliest. The FIFO
    idea aims to reduce the liveness duration of buffers created.
    """

    class NodeInfo(TypedDict):
        indegree: int
        order: int

    node_info: dict[BaseSchedulerNode, NodeInfo] = dict()

    @dataclasses.dataclass
    class NodeWithPriority:
        priority: list[int]
        node: BaseSchedulerNode

        def __lt__(self, other: NodeWithPriority) -> bool:
            if self.priority == other.priority:
                return self.node.mpi_node.index < other.node.mpi_node.index
            return self.priority < other.priority

    def _node_priority(node: BaseSchedulerNode) -> list[int]:
        # priority is the order in which predecessor nodes are executed
        assert node_info[node]["indegree"] == 0
        exec_orders = sorted(
            OrderedSet(
                node_info[pred_node]["order"] for pred_node in node.mpi_node.pred_nodes
            )
        )
        return exec_orders

    # compute nodes' number of unmet dependencies (for schedulability)
    # initialize the list of nodes ready to be scheduled
    nodes_to_schedule: list[NodeWithPriority] = []
    for node in nodes:
        node_info[node] = {"indegree": len(node.mpi_node.pred_nodes), "order": -1}
        if node_info[node]["indegree"] == 0:
            heapq.heappush(
                nodes_to_schedule, NodeWithPriority(_node_priority(node), node)
            )

    # schedule nodes one at a time
    schedule: list[BaseSchedulerNode] = []
    num_iters: int = 0
    while num_iters < len(nodes) and nodes_to_schedule:
        # select a node to schedule
        selected_node = heapq.heappop(nodes_to_schedule).node
        node_info[selected_node]["order"] = len(schedule)
        schedule.append(selected_node)
        num_iters += 1

        # update successor nodes and nodes_to_schedule
        for succ_node in selected_node.mpi_node.succ_nodes:
            assert node_info[succ_node]["indegree"] > 0
            node_info[succ_node]["indegree"] -= 1
            if node_info[succ_node]["indegree"] == 0:
                heapq.heappush(
                    nodes_to_schedule,
                    NodeWithPriority(_node_priority(succ_node), succ_node),
                )

    if num_iters > len(nodes):
        raise RuntimeError("Failed to schedule, while loop ran too long for bfs")

    return schedule
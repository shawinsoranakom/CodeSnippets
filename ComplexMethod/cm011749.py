def reorder_for_minimizing_partition(
        self,
        nodes: list[BaseSchedulerNode],
    ) -> list[BaseSchedulerNode]:
        """
        Reorder nodes to minimize the number of partitions via a bfs
        topological sort. This is the optimal reordering such that the
        number of partitions cannot be reduced further. This may be
        sub-optimal for other metrics such as peak memory. This does not
        change relative orders of two cudagraphable nodes, nor the
        relative order of two non_cudagraphable nodes.
        """
        import heapq

        node_to_indegree: dict[BaseSchedulerNode, int] = dict()
        cudagraphable_nodes: list[tuple[int, BaseSchedulerNode]] = []
        non_cudagraphable_nodes: list[tuple[int, BaseSchedulerNode]] = []
        node_to_index = {node: idx for idx, node in enumerate(nodes)}

        def insert_pending_nodes(node: BaseSchedulerNode) -> None:
            node_with_index = (node_to_index[node], node)
            if self.should_partition(node):
                heapq.heappush(non_cudagraphable_nodes, node_with_index)
            else:
                heapq.heappush(cudagraphable_nodes, node_with_index)

        def update_indegree(node: BaseSchedulerNode) -> None:
            for succ_node in node.mpi_node.succ_nodes:
                assert node_to_indegree[succ_node] > 0
                node_to_indegree[succ_node] -= 1
                if node_to_indegree[succ_node] == 0:
                    insert_pending_nodes(succ_node)

        for node in nodes:
            node_to_indegree[node] = len(node.mpi_node.pred_nodes)
            if node_to_indegree[node] == 0:
                insert_pending_nodes(node)

        schedule: list[BaseSchedulerNode] = []
        num_iters: int = 0
        while num_iters < len(nodes) and (
            non_cudagraphable_nodes or cudagraphable_nodes
        ):
            while non_cudagraphable_nodes:
                _, node = heapq.heappop(non_cudagraphable_nodes)
                schedule.append(node)
                update_indegree(node)

            while cudagraphable_nodes:
                _, node = heapq.heappop(cudagraphable_nodes)
                schedule.append(node)
                update_indegree(node)

            num_iters += 1

        if num_iters > len(nodes):
            raise RuntimeError(
                """
                Failed to schedule, while loop ran too long when
                reordering for minimizing the num of partitions
                """
            )

        return schedule
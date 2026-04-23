def move_non_tensor_nodes_on_boundary(subgraphs: list["Subgraph"]) -> None:
    """
    Move non-tensor nodes on the boundary between subgraphs.

    For each subgraph:

    1. Find nodes whose type is not tensor and any of its children is in another
       subgraph, put them in a queue for next step

    2. Do a BFS on those nodes in the queue,  and run a DFS for each node, let's say node X and it is in subgraph A:

       a. if it is in to_subgraph, return (continue DFS)
       b. if it is in from_subgraph, collect the nodes to nodes_to_move, and continue DFS
       c. otherwise, this means it cannot be moved
       d. also check if node X's parent should be put into the queue. (The queue may
          have duplicated nodes, just process the node once)

    Args:
        subgraphs: List of subgraphs containing nodes to be processed
    """
    # Create a mapping from node to subgraph for quick lookup
    node_to_subgraph: dict[torch.fx.Node, int] = {}
    for i, subgraph in enumerate(subgraphs):
        for node in subgraph.nodes:
            node_to_subgraph[node] = i

    def get_children_in_graph(node: torch.fx.Node) -> list[torch.fx.Node]:
        """Get children nodes that are in callable ops and in some subgraph"""
        return [
            user
            for user in node.users
            if user.op in CALLABLE_NODE_OPS and user in node_to_subgraph
        ]

    def get_parents_in_graph(node: torch.fx.Node) -> list[torch.fx.Node]:
        """Get parent nodes that are in callable ops and in some subgraph"""
        return [
            arg
            for arg in node.all_input_nodes
            if arg.op in CALLABLE_NODE_OPS and arg in node_to_subgraph
        ]

    def has_children_in_other_subgraph(
        node: torch.fx.Node, current_subgraph_idx: int
    ) -> bool:
        """
        Check if the node has any children in a subgraph different from current_subgraph_idx.
        This is the requirement used in both step 1 and step d.
        """
        children = get_children_in_graph(node)
        return any(
            node_to_subgraph[child] != current_subgraph_idx for child in children
        )

    def can_move_node_and_dependencies(
        node: torch.fx.Node, from_subgraph: int, to_subgraph: int
    ) -> tuple[bool, set[torch.fx.Node]]:
        """
        Check if node and its dependencies can be moved from from_subgraph to to_subgraph.
        Returns (can_move, nodes_to_move)

        For node X, do a DFS on its descendants, for each node:
        - if it is in to_subgraph, return (continue DFS)
        - if it is in from_subgraph, collect the nodes to nodes_to_move, and continue DFS
        - otherwise, this means it cannot be moved
        """
        nodes_to_move = set()
        visited = set()
        can_move = True

        def dfs(current_node: torch.fx.Node) -> None:
            nonlocal can_move, nodes_to_move

            if current_node in visited:
                return
            visited.add(current_node)

            # Check current node's subgraph
            if current_node not in node_to_subgraph:
                return  # Skip nodes not in any subgraph

            current_subgraph = node_to_subgraph[current_node]

            if current_subgraph == to_subgraph:
                # If it is in to_subgraph, just end DFS
                return
            elif current_subgraph == from_subgraph:
                # If it is in from_subgraph, collect it and continue DFS
                nodes_to_move.add(current_node)
            else:
                # Otherwise, this means it cannot be moved
                can_move = False
                return

            # Continue DFS on children
            children = get_children_in_graph(current_node)
            for child in children:
                if can_move:  # Only continue if we haven't already failed
                    dfs(child)

        # Start DFS from the original node
        dfs(node)

        return can_move, nodes_to_move

    # For each subgraph, find non-tensor nodes with children in other subgraphs
    for subgraph_idx, subgraph in enumerate(subgraphs):
        # non acc nodes cannot be moved to downstream acc graph, so skip
        if not subgraph.is_acc:
            continue
        # Step 1: Find non-tensor nodes with children in other subgraphs
        queue: list[torch.fx.Node] = []
        processed: set[torch.fx.Node] = set()

        for node in subgraph.nodes:
            # Check if node is non-tensor
            if is_node_output_tensor(node):
                continue

            # Check if node meets step 1 requirement: any children in another subgraph
            if has_children_in_other_subgraph(node, subgraph_idx):
                queue.append(node)

        # Step 2: BFS to move nodes that meet the criteria
        while queue:
            current_node = queue.pop(0)

            # Skip if already processed (queue may have duplicates)
            if current_node in processed:
                continue
            processed.add(current_node)

            # Skip if node is no longer in this subgraph (may have been moved)
            if (
                current_node not in node_to_subgraph
                or node_to_subgraph[current_node] != subgraph_idx
            ):
                continue

            children = get_children_in_graph(current_node)
            if len(children) == 0:
                raise AssertionError(
                    "Only node that has children in other subgraph can be moved"
                )

            # Find target subgraph. The children should all be in the same subgraph except current subgraph
            target_subgraph_candidates = set()
            for child in children:
                child_subgraph = node_to_subgraph[child]
                if child_subgraph != subgraph_idx:
                    target_subgraph_candidates.add(child_subgraph)
            # If multiple children live in different subgraphs, the node cannot be moved. User needs to find other ways to move it.
            if len(target_subgraph_candidates) != 1:
                print(
                    f"Cannot move non-tensor node {current_node.name} on boundary because it has children in multiple subgraphs"
                )
                continue

            target_subgraph = target_subgraph_candidates.pop()

            # Check if we can move this node and its dependencies
            can_move, nodes_to_move = can_move_node_and_dependencies(
                current_node, subgraph_idx, target_subgraph
            )

            if can_move:
                # Move all nodes in nodes_to_move to target subgraph
                for node_to_move in nodes_to_move:
                    # Remove from current subgraph
                    subgraph.nodes.remove(node_to_move)
                    # Add to target subgraph
                    subgraphs[target_subgraph].nodes.append(node_to_move)
                    # Update mapping
                    node_to_subgraph[node_to_move] = target_subgraph
                    print(
                        f"In order move the non-tensor node {current_node.name} on boundary, "
                        f"moved node {node_to_move.name} from {'acc' if subgraph.is_acc else 'gpu'}_{subgraph_idx} "
                        f"to {'acc' if subgraphs[target_subgraph].is_acc else 'gpu'}_{target_subgraph}"
                    )

                # Add parents to the queue if they're non-tensor and not already processed
                # and meet the requirement from step 1 (any children in another subgraph)
                parents = get_parents_in_graph(current_node)
                for parent in parents:
                    if (
                        not is_node_output_tensor(parent)
                        and parent not in processed
                        and parent in node_to_subgraph
                        and node_to_subgraph[parent] == subgraph_idx
                    ):
                        # Check if parent meets step 1 requirement: any children in another subgraph
                        if not has_children_in_other_subgraph(parent, subgraph_idx):
                            raise AssertionError(
                                f"Parent {parent.name} should have children in another subgraph"
                            )
                        queue.append(parent)
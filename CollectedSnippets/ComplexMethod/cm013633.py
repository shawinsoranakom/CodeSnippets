def dfs_iter_find_cycle(all_user_nodes: set[Node]) -> bool:
                for user_node in all_user_nodes:
                    visited_partition_ids = set()

                    for path_node in self.dependency_viewer.downstreams_of(user_node):
                        # If any of the nodes in the dfs path of this node are in the merged_nodes
                        # list then there is a cycle in the graph.
                        if path_node in self_nodes or path_node in other_nodes:
                            return True

                        # If any of the nodes in the dfs path of this node are in the assignment
                        # map then we have to make sure that the partitions that these nodes belong
                        # to do not form a cycle with the current partitions being merged. This means
                        # iterating through all the nodes in all the parititons that are traversed in
                        # the dfs path and checking if they are in the merged_nodes list.
                        if path_node in assignment:
                            partition_id = assignment[path_node]
                            # If the partition id has already been visited then we know that it doesn't
                            # form a cycle with the current partitions being merged.
                            if partition_id in visited_partition_ids:
                                continue
                            p_map = partition_map[partition_id]
                            if self_id in p_map or other_id in p_map:
                                return True

                            visited_partition_ids.add(partition_id)

                return False
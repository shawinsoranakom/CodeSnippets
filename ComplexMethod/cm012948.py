def __next__(self) -> NSSubgraph:
        """
        Returns the next matchable subgraph.
        """
        while len(self.stack) > 0:
            cur_end_node = self.stack.pop()
            if cur_end_node in self.seen_nodes:
                continue

            # for subgraphs which are single nodes, start_node == end_node
            # for subgraphs with more than one node, start node != end_node
            cur_start_node = cur_end_node
            # Subgraphs like linear-relu have the base node as the start node.
            # Subgraphs like dequantize-linear-relu-to(torch.float16) have the
            #   base node as the second node.
            # The cur_base_op_node var will move to the actual node during
            #   the fusion matching later in this code block.
            cur_base_op_node = cur_end_node

            # Check for potential fusions. For now, we are greedy
            # and always skip all non-base nodes of a fusion.  For example,
            # if we match linear-relu backwards, we will always skip the
            # relu node and attempt to match the linear node.  This can
            # be made configurable later if needed.
            for _reverse_fusion_ops, base_op_idx in get_reversed_fusions():
                is_match = end_node_matches_reversed_fusion(
                    cur_end_node, _reverse_fusion_ops, self.gm, self.seen_nodes
                )
                if is_match:
                    # navigate to the base node
                    # pyrefly: ignore [bad-assignment, non-convergent-recursion]
                    for rev_fusion_idx in range(len(_reverse_fusion_ops) - 1):
                        # pyrefly: ignore [bad-argument-type]
                        self.seen_nodes.add(cur_start_node)
                        # for now, assume that there are no other nodes
                        # which need to be added to the stack
                        cur_start_node = cur_start_node.args[0]  # type: ignore[assignment]
                        # if the base op index matches the current node, set it
                        rev_base_op_idx = len(_reverse_fusion_ops) - 2 - base_op_idx
                        if rev_fusion_idx == rev_base_op_idx:
                            cur_base_op_node = cur_start_node
                    break

            # pyrefly: ignore [bad-argument-type]
            self.seen_nodes.add(cur_start_node)
            # add args of previous nodes to stack
            # pyrefly: ignore [missing-attribute]
            for arg in cur_start_node.all_input_nodes:
                self._recursively_add_node_arg_to_stack(arg)

            # skip unmatchable nodes
            # note: this check is done on the start_node, i.e.
            # if we are matching linear-relu in reverse, this would do the matchable
            # check on the linear
            # pyrefly: ignore [bad-argument-type]
            if not self._is_matchable(cur_base_op_node):
                continue

            # If an observer or a fake_quant was not matched as a part of
            # a pattern of multiple nodes, ignore it. One case where this is
            # relevant is an observer on a graph input, which was added because
            # it is necessary for the next node.
            if cur_end_node.op == "call_module" and cur_start_node is cur_end_node:
                maybe_obs = getattr_from_fqn(self.gm, cur_end_node.target)  # type: ignore[arg-type]
                if isinstance(maybe_obs, (ObserverBase, FakeQuantizeBase)):
                    continue

            return NSSubgraph(
                # pyrefly: ignore [bad-argument-type]
                start_node=cur_start_node,
                end_node=cur_end_node,
                # pyrefly: ignore [bad-argument-type]
                base_op_node=cur_base_op_node,
            )

        raise StopIteration
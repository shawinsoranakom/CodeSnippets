def _block_traverse_impl(
        self, nodes: NodeList, start_idx: int, end_idx: int, find_last_node: bool
    ) -> int | None:
        """
        Recursive block search implementation.
        find_last_node: If True, search for the last node which result in numerics difference
        if False: find first node in sorted node list
        """
        report: list[str] = []

        mid = (start_idx + end_idx) // 2
        cur_nodes_list: NodeList = nodes[: mid + 1] if find_last_node else nodes[mid:]

        if self.exclusion_fn:
            self.exclusion_fn(cur_nodes_list, -1, -1)

        cur_nodes = set(cur_nodes_list)

        first_node_name = cur_nodes_list[0].name
        last_node_name = cur_nodes_list[-1].name
        target_node_name = last_node_name if find_last_node else first_node_name

        self.iteration += 1
        self.reports.append(report)
        report.extend(
            [
                "=" * 30,
                f"Block search iteration {self.iteration}",
            ]
        )
        report.extend(
            [
                f"Search for {'last' if find_last_node else 'first'} node in culprits",
                f"From node index {start_idx}:{nodes[start_idx].name} to {end_idx}:{nodes[end_idx].name}. ",
                f"Subgraph constructed by {first_node_name} to {last_node_name}",
                f"Targeting node: {target_node_name}",
                f"Size of the interested node list is {end_idx - start_idx + 1}",
            ]
        )
        report_idx = len(self.reports) - 1

        try:
            split_module, submod_name = self._build_submodule(cur_nodes)
            self._run_and_compare(
                split_module, submod_name, [last_node_name], report_idx
            )
        except (FxNetMinimizerResultMismatchError, FxNetMinimizerRunFuncError):
            report.append(
                f"Culprits found from node {first_node_name} to {last_node_name}."
            )

            if start_idx == mid == end_idx:
                report.extend(
                    [
                        "This is the last node in the sub-module. ",
                        "Search in the current branch is successful with node :",
                        f"{start_idx}, node name: {nodes[start_idx].name}.",
                    ]
                )
                self.print_report(report)
                return start_idx

            report.append(
                "Proceed to split and lower the halves of the current "
                "sub-module individually."
            )
            self.print_report(report)

            if find_last_node:
                return self._block_traverse_impl(nodes, start_idx, mid, find_last_node)
            else:
                return self._block_traverse_impl(
                    nodes, mid + 1, end_idx, find_last_node
                )
        else:
            report.append(
                f"Culprits not found from node start to {mid}:{nodes[mid].name}."
            )

            if start_idx == mid == end_idx:
                # We did not find anything if the pointers have not moved
                if (start_idx == 0 and not find_last_node) or (
                    start_idx == len(nodes) - 1 and find_last_node
                ):
                    report.append(
                        f"At {'last' if find_last_node else 'first'} node, no culprits found."
                    )
                    self.print_report(report)
                    return None

                # Otherwise, we have converged on the border between discrepancy and valid
                return start_idx + (1 if find_last_node else -1)

            report.append(
                "Proceed to split and lower the halves of the current "
                "sub-module individually."
            )
            self.print_report(report)

            if find_last_node:
                return self._block_traverse_impl(
                    nodes, mid + 1, end_idx, find_last_node
                )
            else:
                return self._block_traverse_impl(nodes, start_idx, mid, find_last_node)
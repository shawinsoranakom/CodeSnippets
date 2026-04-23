def _block_traverse(self, nodes: NodeList, find_last_node: bool | None) -> NodeSet:
        """
        Traverse topologically sorted node list
        Find minimum block (start_idx, end_idx) which contains the culprit
        1st pass: search for end_idx by finding the last node in culprit block
        where Numerical accuracy (0, end_idx) > threshold
        2nd pass: search for start_idx by finding the first node in culprit block
        where Numerical accuracy (start_idx, end_idx) < threshold
        Form minimum block by (start_idx - 1, end_idx)
        """
        culprits: NodeSet = set()
        first_node_name = nodes[0].name
        last_node_name = nodes[-1].name
        last_node_report = [f"Block search from {first_node_name} to {last_node_name}"]
        last_node_report.append("*" * 50)
        self.reports.append(last_node_report)

        start_idx = 0
        end_idx = len(nodes) - 1

        final_start_idx: int | None = start_idx
        final_end_idx: int | None = end_idx

        run_both = find_last_node is None

        # step 1: find (0, end_idx) of culprit block
        if run_both or find_last_node:
            last_node_report.append("Start searching for last node in culprit")
            self.print_report(last_node_report)
            final_end_idx = self._block_traverse_impl(nodes, start_idx, end_idx, True)

            if final_end_idx is None:
                last_node_report.append("No culprits found")
                self.print_report(last_node_report)
                return culprits

            last_node_report.extend(
                [
                    "Finish Pass 1",
                    f"Find end_idx = {final_end_idx}:{nodes[final_end_idx].name}",
                ]
            )
            self.print_report(last_node_report)

        # step 2: reduce culprit block to (start_idx, end_idx)
        if run_both or not find_last_node:
            first_node_report = ["Start searching for first node in culprit"]
            self.print_report(first_node_report)
            final_start_idx = self._block_traverse_impl(
                nodes[0 : end_idx + 1], start_idx, final_end_idx or end_idx, False
            )

            if final_start_idx is None:
                last_node_report.append("No culprits found")
                self.print_report(last_node_report)
                return culprits

            first_node_report.append("*" * 50)
            self.reports.append(first_node_report)
            first_node_report.extend(
                [
                    "Finish Pass 2",
                    f"Find start_idx = {final_start_idx}:{nodes[final_start_idx].name}",
                ]
            )
            self.print_report(first_node_report)

        # step 3: form module with minimum culprits. These indexes are guaranteed to exist
        range_start, range_end = cast(int, final_start_idx), cast(int, final_end_idx)
        culprits.update(nodes[range_start : range_end + 1])
        result_report = [
            f"Finish searching, found minimum block ({nodes[range_start]},{nodes[range_end]})"
        ]
        self.reports.append(result_report)
        self.print_report(result_report)
        return culprits
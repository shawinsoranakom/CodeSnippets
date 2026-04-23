def _binary_search_impl(
        self, all_nodes: NodeList, start_idx: int, end_idx: int
    ) -> NodeSet:
        """
        Recursive binary search implementation.
        """
        culprits: NodeSet = set()
        nodes: NodeList = all_nodes[start_idx:end_idx]

        report: list[str] = []
        if self.exclusion_fn is not None:
            self.exclusion_fn(nodes, start_idx, end_idx)
            if len(nodes) == 0:
                report = ["All nodes are excluded by user"]
                self.reports.append(report)
                return culprits

        first_node_name = nodes[0].name
        output_node_name = nodes[-1].name
        self.iteration += 1
        self.reports.append(report)
        report.append(f"Binary search iteration {self.iteration}")
        report.append(
            f"From node index {start_idx}:{first_node_name} to {end_idx - 1}:{output_node_name}. "
            f"Size of the interested node list is {len(nodes)}"
        )
        cur_nodes: NodeSet = set(nodes)

        try:
            split_module, submod_name = self._build_submodule(cur_nodes)
            self._run_and_compare(split_module, submod_name, [output_node_name])

        except (FxNetMinimizerRunFuncError, FxNetMinimizerResultMismatchError):
            if len(nodes) == 1:
                report.append(
                    f"This is the last node in the sub-module. "
                    f"Search in the current branch is successful with culprit = {cur_nodes}."
                )
                self.print_report(report)
                return cur_nodes

            report.append(
                "Proceed to split and lower the halves of the current "
                "sub-module individually."
            )
            self.print_report(report)

            mid = len(nodes) // 2
            culprits = self._binary_search_impl(all_nodes, start_idx, start_idx + mid)

            if len(culprits) != 0 and not self.settings.find_all:
                return culprits

            culprits = self._binary_search_impl(all_nodes, start_idx + mid, end_idx)

            if len(culprits) == 0:
                report.append(
                    f"Further split and lowering found no errors. "
                    f"Unable to minimize the submodule with list of nodes: {nodes}"
                )
                self.print_report(report)

            return culprits
        else:
            report.append("No discrepancy found.")
            self.print_report(report)
            return set()
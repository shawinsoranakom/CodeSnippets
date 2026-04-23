def _accumulate_traverse(self, nodes: NodeList) -> NodeSet:
        culprits: NodeSet = set()
        nodes_to_run: NodeSet = set()

        # find_all is not supported for accumulate traversal because all the
        # ops run on NNPI. So we return after the first op that raises error.
        if self.settings.find_all:
            print("'Find All' mode is not supported in accumulate traversal.")
            return culprits

        for node in nodes:
            report: list[str] = []
            self.reports.append(report)
            self.iteration += 1
            report.append(f"Accumulate traverse iteration {self.iteration}.")

            nodes_to_run.add(node)

            node_name = node.name
            if node_name is not None and isinstance(node_name, tuple):
                node_name = node_name[0]
            if node_name is None or not isinstance(node_name, str):
                raise AssertionError(f"minimize: node_name: {node_name}")

            report.append(f"Add node: {node_name}")

            try:
                split_module, submod_name = self._build_submodule(nodes_to_run)
                self._run_and_compare(split_module, submod_name, [node_name])
                self.print_report(report)
            except (FxNetMinimizerResultMismatchError, FxNetMinimizerRunFuncError):
                culprits.add(node)
                report.append(f"Found culprit {node}")
                self.print_report(report)
                return culprits

        return culprits
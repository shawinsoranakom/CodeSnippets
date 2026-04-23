def _sequential_traverse(self, nodes: NodeList) -> NodeSet:
        """
        Traverse `nodes` one by one and determine if any of them is a culprit.
        """
        culprits: NodeSet = set()

        for node in nodes:
            report: list[str] = []
            self.reports.append(report)
            self.iteration += 1
            report.append(f"Sequential traverse iteration {self.iteration}.")
            report.append(f"Visit node: {node.name}")

            _LOGGER.info("Visit node: %s", node.name)
            node_list: NodeList = [node]
            if self.exclusion_fn is not None:
                self.exclusion_fn(node_list, -1, -1)
                if len(node_list) == 0:
                    report.append(f"User exclusion : {node.name}")
                    self.print_report(report)
                    if not self.settings.find_all:
                        return culprits
                    else:
                        continue

            cur_nodes: NodeSet = {node}

            if node in self.fusions:
                cur_nodes = self.fusions[node]

            try:
                split_module, submod_name = self._build_submodule(cur_nodes)
                self._run_and_compare(split_module, submod_name, [node.name])
                self.print_report(report)
            except FxNetMinimizerResultMismatchError:
                culprits.add(node)
                report.append(f"Found culprit from numeric error: {node}")
                self.print_report(report)
                if not self.settings.find_all:
                    return culprits
            except FxNetMinimizerRunFuncError:
                culprits.update(cur_nodes)
                report.append(f"Found culprit from run error: {node}")
                self.print_report(report)
                if not self.settings.find_all:
                    return culprits

        return culprits
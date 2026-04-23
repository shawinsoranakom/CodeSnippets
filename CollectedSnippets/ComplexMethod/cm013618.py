def _run_and_compare(
        self,
        split_module: torch.fx.GraphModule,
        submod_name: str,
        output_names: Names,
        report_idx: int = -1,
    ) -> None:
        """
        Run the submodule in `split_module` that has name `submod_name`
        using `self.run_a` and `self.run_b` and compare their results.

        Args:
            split_module: Main module that contains the minimize submodule.
            submod_name: Name of the minimize submodule.
            output_names: Names of the node we want to output. If None, we
                will use the original output.
        """
        submodule = getattr(split_module, submod_name)
        a_input, b_input = self._get_submod_inputs(split_module, submod_name)

        if len(self.reports) == 0:
            self.reports.append([])
            self.iteration = 1

        report = self.reports[report_idx if report_idx >= 0 else self.iteration - 1]
        report.append("Run and compare ...")

        if output_names and not self.settings.all_outputs:
            output_nodes: NodeList = []
            for node in submodule.graph.nodes:
                if node.op == "output":
                    submodule.graph.erase_node(node)

                if node.name in output_names:
                    output_nodes.append(node)

            submodule.graph.output(
                output_nodes[0] if len(output_nodes) == 1 else tuple(output_nodes)
            )
            submodule.graph.lint()
            submodule.recompile()

        # Use name of args in output node as key to store comparison result
        for node in submodule.graph.nodes:
            if node.op == "output":
                result_key = map_arg(node.args, lambda x: x.name)

        try:
            a_result = self.run_a(submodule, a_input, report_idx)
            b_result = self.run_b(submodule, b_input, report_idx)
            self._store_outputs(a_result, b_result, submodule)
        except Exception as e:
            report.append(f"Exception raised when running {submod_name}: {e}")
            raise FxNetMinimizerRunFuncError(  # noqa: B904
                f"Exception raised when running {submod_name}: {e}"
            )

        # Compare results
        names: Names = output_names
        if output_names is None:
            names = [str(v) for v in result_key]  # type: ignore[possibly-undefined]

        numeric_result, bool_result = self.compare_fn(a_result, b_result, names)

        self.results[result_key] = numeric_result  # type: ignore[possibly-undefined]
        report.append(f"Numerical accuracy = {numeric_result}")
        if not bool_result:
            report.append(f"Result mismatch for {result_key}")  # type: ignore[possibly-undefined]
            if self.module_exporter:
                if isinstance(result_key, tuple):  # type: ignore[possibly-undefined]
                    # pyrefly: ignore [unbound-name]
                    result_key = result_key[-1]
                # If the result is still a tuple (happens in non-sequential mode),
                # we only use the first element as name.
                if isinstance(result_key, tuple):  # type: ignore[possibly-undefined]
                    # pyrefly: ignore [unbound-name]
                    result_key = str(result_key[0])
                # pyre-ignore[29]: not a function
                self.module_exporter(
                    a_input,
                    submodule,
                    # pyrefly: ignore [unbound-name]
                    result_key + "_cpu",
                )
                # pyre-ignore[29]: not a function
                self.module_exporter(
                    b_input,
                    submodule,
                    # pyrefly: ignore [unbound-name]
                    result_key + "_acc",
                )
            raise FxNetMinimizerResultMismatchError(f"Result mismatch for {result_key}")
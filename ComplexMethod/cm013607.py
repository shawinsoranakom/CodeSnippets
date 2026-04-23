def split_preview(self, dump_graph: bool = False) -> str:
        reports = ""
        subgraphs = self.put_nodes_into_subgraphs()
        acc_subgraphs_num = len([g for g in subgraphs if g.is_acc])
        cpu_subgraphs_num = len(subgraphs) - acc_subgraphs_num
        reports += f"Before removing small acc subgraphs, total {len(subgraphs)} subgraphs are created:"
        reports += f" {acc_subgraphs_num} acc subgraphs and {cpu_subgraphs_num} cpu subgraphs.\n"

        subgraphs = self.remove_small_acc_subgraphs(subgraphs)
        acc_subgraphs_num = len([g for g in subgraphs if g.is_acc])
        cpu_subgraphs_num = len(subgraphs) - acc_subgraphs_num
        reports += f"After removing small acc subgraphs, total {len(subgraphs)} subgraphs are created:"
        reports += f" {acc_subgraphs_num} acc subgraphs and {cpu_subgraphs_num} cpu subgraphs.\n"

        for i, subgraph in enumerate(subgraphs):
            reports += (
                f"_run_on_acc_{i}: "
                if subgraph.is_acc
                else f"{self.non_acc_submodule_name}{i}: "
            )
            reports += f"{len(subgraph.nodes)} node(s)\n"

        self.tag(subgraphs)
        split_mod = self.split(remove_tag=True)
        split_mod.eval()

        if dump_graph:
            drawer = FxGraphDrawer(split_mod, "preview", ignore_getattr=True)
            dot_graphs = drawer.get_all_dot_graphs()
            for name, dot_graph in dot_graphs.items():
                # pyre-fixme[16]: `pydot.Dot` has no attribute `write_raw`.
                dot_graph.write_raw(f"{name}.dot")  # type: ignore[attr-defined]

        max_qps: float = self.PCIe_BW
        bottleneck_module = ""

        for node in split_mod.graph.nodes:
            if node.op == "call_module" and "acc" in node.target:
                reports += f"\nProcessing acc submodule {node.target}\n"

                submod = getattr(split_mod, node.target)

                def get_submod_inputs(
                    main_mod: torch.fx.GraphModule,
                    submod: torch.fx.GraphModule,
                    example_inputs: Sequence[Any],
                ) -> tuple[Any, ...]:
                    sub_inputs: tuple[Any, ...] | None = None

                    def get_inputs(
                        self: torch.nn.Module, inputs: tuple[Any, ...]
                    ) -> None:
                        nonlocal sub_inputs
                        sub_inputs = inputs

                    handle = submod.register_forward_pre_hook(get_inputs)
                    main_mod(*example_inputs)
                    handle.remove()
                    if sub_inputs is None:
                        raise AssertionError("Forward pre-hook did not capture inputs")
                    return sub_inputs

                submod_inputs = get_submod_inputs(split_mod, submod, self.sample_input)
                ShapeProp(submod).propagate(*submod_inputs)

                total_input_bytes = 0
                total_output_bytes = 0

                reports += "Checking inputs...\n"
                for n in submod.graph.nodes:
                    if n.op == "placeholder":
                        if not is_node_output_tensor(n):
                            reports += f"Input {n.name} is not a tensor, this might cause problems during lowering!\n"
                        else:
                            total_input_bytes += get_size_of_node(submod, n)[0]
                    if n.op == "output":
                        output_node = n

                reports += "Checking outputs...\n"

                def get_bytes(node: torch.fx.Node) -> None:
                    nonlocal total_output_bytes
                    nonlocal reports
                    if not is_node_output_tensor(node):
                        reports += f"Output {node.name} is not a tensor, this might cause problems during lowering!\n"
                    else:
                        total_output_bytes += get_size_of_node(submod, node)[0]

                map_arg(output_node.args, get_bytes)  # type: ignore[possibly-undefined]
                qps = self.PCIe_BW / max(total_input_bytes, total_output_bytes)
                reports += f"Total input size in bytes is {total_input_bytes}, total output size in bytes is {total_output_bytes},"
                reports += f" theoretical max qps (bounds by PCIe bandwidth) for this submodule is {qps}.\n"

                if qps < max_qps:
                    max_qps = qps
                    bottleneck_module = node.target

                try:
                    lowered_submod = self._lower_model_to_backend(submod, submod_inputs)
                except RuntimeError:
                    reports += "Run into an error during lowering!\n"
                    reports += self._find_culprit(submod, submod_inputs)
                    continue

                try:
                    lowered_submod(*submod_inputs)
                except RuntimeError:
                    reports += "Run into an error during inference!\n"
                    reports += self._find_culprit(submod, submod_inputs)
                else:
                    reports += "Lowering and running succeed!\n"

        reports += f"\nTheoretical max qps (bounds by PCIe bandwidth) for this model is {max_qps},"
        reports += f" bottleneck is submodule {bottleneck_module}."
        print(reports)

        # return the reports for testing purposes
        return reports
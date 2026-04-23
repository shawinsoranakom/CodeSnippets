def _compute_sym_input_values(self) -> list[int]:
        """Extract concrete dimension values for sym_inputs from benchmark_inputs.

        The compiled module expects symbolic dimension values as runtime arguments.
        This maps each symbolic variable to its concrete value from the benchmark tensors.
        Used for range based autotuning.
        """
        sym_input_names = OrderedSet(
            [s.name for s in self.sym_inputs if hasattr(s, "name")]
        )

        # Build mapping: symbolic dimension name -> concrete value
        sym_name_to_value: dict[str, int] = {}
        for inp_node, benchmark_inp in zip(self.input_nodes, self.benchmark_inputs):
            if isinstance(benchmark_inp, torch.Tensor):
                for sym_dim, actual_dim in zip(
                    inp_node.get_size(), benchmark_inp.shape
                ):
                    if isinstance(sym_dim, sympy.Symbol):
                        sym_name_to_value[sym_dim.name] = int(actual_dim)
                    elif str(sym_dim) in sym_input_names:
                        sym_name_to_value[str(sym_dim)] = int(actual_dim)

        result = []
        for sym_var in self.sym_inputs:
            if isinstance(sym_var, sympy.Symbol) and sym_var.name in sym_name_to_value:
                result.append(sym_name_to_value[sym_var.name])
            else:
                hint = V.graph.sizevars.shape_env.optimization_hint(sym_var, fallback=1)
                result.append(int(hint))
        return result
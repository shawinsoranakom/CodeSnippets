def _find_eligible_epilogues(self, epilogue_nodes, output_param_mapping):
        """Compute fusion eligibility and register extra inputs.

        Returns list of eligible epilogue tuples:
            [(snode, output_buf, output_param, store_target), ...]
        """
        from torch._inductor.dependencies import MemoryDep

        # Filter eligible epilogues
        epilogues = []
        for epilogue_node in epilogue_nodes:
            if isinstance(epilogue_node.node, ir.MultiOutput):
                continue
            dep_names = OrderedSet(
                d.name
                for d in epilogue_node.read_writes.reads
                if isinstance(d, MemoryDep) and d.name in output_param_mapping
            )
            if len(dep_names) != 1:
                continue
            output_buf = next(iter(dep_names))
            epilogue_writes = epilogue_node.read_writes.writes
            raw_st = next(iter(epilogue_writes)).name if epilogue_writes else None
            epilogues.append(
                (
                    epilogue_node,
                    output_buf,
                    output_param_mapping[output_buf],
                    raw_st if raw_st != output_buf else None,
                )
            )

        # Register extra inputs needed by fused epilogues
        for snode, _, _, _ in epilogues:
            for dep in snode.read_writes.reads:
                if isinstance(dep, MemoryDep) and dep.name not in output_param_mapping:
                    if dep.name not in self._extra_inputs:
                        param = f"_extra_input_{len(self._extra_inputs)}"
                        self._extra_inputs[dep.name] = param
                        self.args.input_buffers[dep.name] = param

        return epilogues
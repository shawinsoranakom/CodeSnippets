def remap_input(self, x):
        if x.graph is not self.flat_graph:
            raise AssertionError(
                "expected x.graph to be flat_graph, got different graph"
            )
        if x in self.node_map:
            return self.node_map[x]
        self.print(f"remap_input({x})")
        if x in self.node_to_placeholder:
            return self.node_to_placeholder[x]
        elif (
            x.op == "placeholder" or self.module_call_graph.get(self.fqn) is None
            # allow placeholder creation if we are not preserving module call signature
        ):
            self.add_placeholder(x)
            if self.parent_call_module is not None:
                # Important to *prepend* the output to match how we are
                # inserting placeholder nodes.
                with self.parent.graph.inserting_before(self.parent_call_module):
                    self.parent_call_module.insert_arg(0, self.parent.remap_input(x))
            return self.node_to_placeholder[x]
        elif x.op == "call_function" and (
            x.target
            in (
                torch.ops.aten.sym_size.int,
                torch.ops.aten.item.default,
                torch.ops.aten.unbind.int,
                torch.ops.aten.sum.dim_IntList,
                torch.ops.aten.view.default,
                torch.ops.aten.diff.default,
            )
            or (hasattr(x.target, "__module__") and x.target.__module__ == "_operator")
        ):
            # export deduplicates sym_size nodes, and may need to re-copy them
            # if module call signature needs to be preserved
            self.copy_sym_call_function(x)
            return self.node_map[x]
        elif self.module_call_graph.get(self.fqn) is not None:
            # x is reading the intermediate value of a mutation, so record it;
            # later we will find where it was created and perform the update
            return self.ivals.read(self, x)  # type: ignore[operator, union-attr]
        else:
            raise RuntimeError(
                f"Could not run remap_input() on op type: {x.op} for node {x}"
            )
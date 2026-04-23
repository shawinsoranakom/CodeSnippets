def run_node(self, n: Node) -> Any:
        from torch.fx.experimental.symbolic_shapes import (
            compute_unbacked_bindings,
            rebind_unbacked,
        )

        if (
            n.op == "call_function"
            and n.target is torch.ops.higher_order.invoke_subgraph
            and n.args[1] not in self.seen_subgraphs
        ):
            # Prevent redundant fake tensor prop for invoke_subgraphs. Note that
            # there is also fake tensor caching for the entire subgraph. This
            # happens the next time we call `run_node` for the same subgraph,
            # which goes through super.run_node and caches the fake tensor prop.
            # Therefore, we are propagating fake tensor through the subgraphs
            # twice.
            if not isinstance(n.args[1], str):
                raise AssertionError(f"Expected str, got {type(n.args[1])}")
            if not (
                isinstance(n.args[0], torch.fx.Node)
                and n.args[0].op == "get_attr"
                and isinstance(n.args[0].target, str)
            ):
                raise AssertionError(
                    "Expected n.args[0] to be a get_attr Node with str target"
                )
            self.seen_subgraphs.add(n.args[1])
            operands = n.args[2:]
            example_inputs = []
            for operand in operands:
                if not (isinstance(operand, torch.fx.Node) and "val" in operand.meta):
                    raise AssertionError("Expected Node with 'val' in meta")
                example_inputs.append(operand.meta["val"])
            return FakeTensorProp(
                getattr(self.module, n.args[0].target), mode=self._mode
            ).propagate(*example_inputs)

        result = super().run_node(n)
        rebind_unbacked(self._mode.shape_env, n, result)

        def extract_val(obj: Any) -> Any:
            if isinstance(obj, FakeTensor):
                return snapshot_fake(obj)
            elif isinstance(obj, torch.Tensor):
                # TODO: How is it possible that we get a non fake tensor?  We
                # should be running under the mode...
                return snapshot_fake(self._mode.from_tensor(obj, static_shapes=True))
            elif isinstance(obj, py_sym_types):
                return obj
            else:
                return None

        meta = map_aggregate(result, extract_val)
        if meta is not None:
            n.meta["val"] = meta
            if (shape_env := self._mode.shape_env) and (
                symbol_to_path := compute_unbacked_bindings(shape_env, result)
            ):
                n.meta["unbacked_bindings"] = symbol_to_path

        return result
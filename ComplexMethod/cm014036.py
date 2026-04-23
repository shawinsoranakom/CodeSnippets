def _lift_symbols_in_symint(
            s: int | torch.SymInt,
            source: Source | None,
            before: bool = False,
        ) -> None:
            if not is_symbolic(s):
                return

            assert isinstance(s, torch.SymInt)
            self_to_be_bound = self.lookup_unbound_symbols(s)
            if len(self_to_be_bound) == 0:
                return

            # For subgraph
            if self.parent is not None:
                # Recursively lift symbols in symint until top-level.
                self.parent._lift_basic_symbols(s, source)
                for s0 in self_to_be_bound:
                    parent_proxy = self.parent.bound_symbols[s0]
                    example_val = parent_proxy.node.meta["example_value"]  # type: ignore[union-attr]
                    assert isinstance(example_val, torch.SymInt)
                    ph = self.create_graph_input(
                        str(s0),
                        type(example_val),
                        example_val,
                        before=before,
                        source=source,
                    )
                    log.debug(
                        "_lift_symbols_in_symint %s from %s at debug_level %s",
                        s0,
                        source.name if source is not None else "subgraph inputs",
                        self.debug_level,
                    )
                    self.lifted_freevars[parent_proxy] = ph  # type: ignore[index]
            # For root_tracer:
            else:
                assert len(self_to_be_bound) == 1, (
                    f"For root tracer, we only expect to bind basic symbols (compound symbols "
                    f"should be cached before) but got unbound symbols {self_to_be_bound} in {s}"
                )
                assert source is not None, (
                    f"Source of '{s}' is None when lifting it to input of top-level. If it's an unbacked symbol, "
                    "this could be because it's not tracked with lazy_bind_unbacked_symbols. "
                    f"Otherwise, should provide a source when create_graph_input for `{s}` at root tracer."
                )
                s0 = next(iter(self_to_be_bound))
                ph = self.create_graph_input(
                    str(s0),
                    type(s),
                    s,
                    before=before,
                    source=source,
                )
                log.debug(
                    "_lift_symbols_in_symint %s from %s at debug_level %s",
                    s,
                    source.name if source is not None else "subgraph inputs",
                    self.debug_level,
                )
                ph.node.meta["grapharg"] = GraphArg(
                    source,
                    s,
                    pass_arg_as_tensor=False,
                    fake_tensor=None,
                    is_tensor=False,
                )
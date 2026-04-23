def apply(self, gm: torch.fx.GraphModule | torch.fx.Graph) -> int:
        """Apply all registered patterns to the graph, returning the number of matches."""
        if not self.patterns:
            return 0
        if isinstance(gm, torch.fx.GraphModule):
            graph = gm.graph
        elif isinstance(gm, torch.fx.Graph):
            graph = gm
            gm = graph.owning_module
        else:
            raise RuntimeError(
                f"The input to PatternMatcherPass must be a GraphModule or a Graph, but got {type(gm)}"
            )
        if should_compute_mutation_region_ids(graph):
            compute_mutation_region_ids(graph)
        get_mutation_region_id_partial = functools.partial(
            get_mutation_region_id, graph
        )
        count = 0
        nodes = []
        has_call_module = False
        for op, target in self.patterns:
            if op == "call_module":
                has_call_module = True
            else:
                nodes.append(graph.find_nodes(op=op, target=target, sort=False))
        if has_call_module:
            nodes.append(graph.find_nodes(op="call_module", sort=False))
        pass_name = self.pass_name if self.pass_name is not None else "pattern_matcher"
        assert isinstance(gm, torch.fx.GraphModule)
        with GraphTransformObserver(gm, pass_name, self.subsystem):
            for node in sorted(itertools.chain.from_iterable(nodes), reverse=True):
                target = extract_target(node)
                if node.op == "call_module":
                    if (node.op, target) not in self.patterns:
                        continue

                # conservatively not applying pattern for cpu input,
                # since some of the patterns induce codegen and split nodes.
                # Note: we will only skip cpu compute if disable_cpp_codegen=True
                if fallback_node_due_to_unsupported_type(node, allow_cpu_inputs=False):
                    continue

                for entry in self.patterns[(node.op, target)]:
                    if node._erased:
                        break
                    m = entry.pattern.match(node)
                    # pattern match crosses mutation barrier - discard
                    if (
                        is_match(m)
                        and len(
                            OrderedSet(map(get_mutation_region_id_partial, m.nodes))
                        )
                        != 1
                    ):
                        continue
                    # pattern match crosses stream boundary - discard
                    if (
                        is_match(m)
                        and len(
                            OrderedSet(
                                n.meta.get("custom", {}).get("stream", 0)
                                for n in m.nodes
                            )
                        )
                        != 1
                    ):
                        continue
                    if _should_debug_node(node.name):
                        log.warning("%s%s %s %s", node, node.args, m, entry.pattern)

                    if is_match(m) and guard_or_false(entry.extra_check(m)):
                        count += 1
                        entry.apply(m, graph, node)
                        counters[backend]["pattern_matcher_count"] += 1
                        counters[backend]["pattern_matcher_nodes"] += len(m.nodes)

                        # Track per-pattern counts when debug mode is active
                        if os.environ.get("TORCHINDUCTOR_PATTERN_MATCH_DEBUG"):
                            if getattr(entry, "pattern_name", None):
                                pattern_name = entry.pattern_name
                            else:
                                # Fallback: use pattern class name + operation target
                                pattern_class = entry.pattern.__class__.__name__
                                target = str(node.target)
                                pattern_name = f"{pattern_class}_{target}"

                            pattern_key = f"{backend}_pattern_matcher_per_pattern"
                            counters[pattern_key][pattern_name] += 1
        return count
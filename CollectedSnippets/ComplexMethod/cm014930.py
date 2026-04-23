def test_subgraph_matcher(self, test_model):

        setup = getattr(test_model, "setup", None)
        if callable(setup):
            setup()

        traced = symbolic_trace(test_model.forward)
        pattern_traced = symbolic_trace(test_model.pattern)

        for test_case in test_model.test_cases:

            matcher = SubgraphMatcher(pattern_traced.graph,
                                      match_output=test_case.match_output,
                                      match_placeholder=test_case.match_placeholder,
                                      remove_overlapping_matches=test_case.remove_overlapping_matches)
            matches = matcher.match(traced.graph)

            if len(matches) != test_case.num_matches:
                raise AssertionError(f"match count mismatch: {len(matches)} != {test_case.num_matches}")

            for match in matches:
                for node in pattern_traced.graph.nodes:
                    if not test_case.match_placeholder and node.op == "placeholder":
                        continue
                    if not test_case.match_output and node.op == "output":
                        continue
                    if node not in match.nodes_map:
                        raise AssertionError(f"node {node} not in match.nodes_map")

        tearDown = getattr(test_model, "tearDown", None)
        if callable(setup):
            tearDown()
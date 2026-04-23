def __init__(
        self,
        pattern: Graph,
        match_output: bool = False,
        match_placeholder: bool = False,
        remove_overlapping_matches: bool = True,
        ignore_literals: bool = False,
    ) -> None:
        """
        Args:
            pattern: the targeted matching pattern, represented in fx.Graph.
            match_output: If True, output node in the pattern graph will be treated as a part of the targeted pattern.
                If False, output node is ignored during match.
            match_placeholder: If True, placeholder node in the pattern graph will be treated as a part of
                the targeted pattern. If False, placeholder nodes will be used a wildcard.
            remove_overlapping_matches: If True, in the case of overlapping matches, only the first match
                will be returned.
            ignore_literals: If True, will not check if literals are equal and
                will instead treat them as wildcards.
        """

        self.pattern = pattern
        self.match_output = match_output
        self.match_placeholder = match_placeholder
        self.remove_overlapping_matches = remove_overlapping_matches
        self.ignore_literals = ignore_literals

        if len(pattern.nodes) == 0:
            raise ValueError(
                "SubgraphMatcher cannot be initialized with an empty pattern"
            )

        for node in pattern.nodes:
            if node.op != "output" and not node.is_impure():
                if len(node.users) == 0:
                    raise AssertionError(
                        "SubgraphMatcher cannot be initialized with an pattern with dead code"
                    )

        # TODO: assert pattern is a connected graph

        self.pattern_placeholder_nodes = [
            n for n in pattern.nodes if n.op == "placeholder"
        ]
        output_node = next(iter(reversed(pattern.nodes)))
        # nodes returned by outputs
        self.pattern_returning_nodes: list[Node] = output_node.all_input_nodes

        self.pattern_anchors: list[Node] = []
        if match_output:
            self.pattern_anchors = [output_node]
        else:
            # If a node has output_node as the ONLY user, then this node is a graph sink,
            # and should be matched against as an anchor
            self.pattern_anchors = [
                n for n in output_node.all_input_nodes if len(n.users) == 1
            ]
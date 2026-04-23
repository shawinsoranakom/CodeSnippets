def test_matcher_with_name_node_map_module(self):
        """Testing SubgraphMatcherWithNameNodeMap with module pattern"""

        class M(torch.nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.linear = torch.nn.Linear(5, 5)

            def forward(self, x):
                return self.linear(x)

        class Pattern(torch.nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.linear = torch.nn.Linear(5, 5)

            def forward(self, x):
                linear = self.linear(x)
                # Note: we can't put "weight": self.linear.weight in dictionary since
                # nn.Parameter is not an allowed output type in dynamo
                return linear, {"linear": linear, "x": x}

        example_inputs = (torch.randn(3, 5),)
        pattern_gm = export(Pattern(), example_inputs, strict=True).module()
        matcher = SubgraphMatcherWithNameNodeMap(pattern_gm)
        target_gm = export(M(), example_inputs, strict=True).module()
        internal_matches = matcher.match(target_gm.graph)
        for internal_match in internal_matches:
            name_node_map = internal_match.name_node_map
            if "linear" not in name_node_map:
                raise AssertionError("Expected 'linear' in name_node_map")
            if "x" not in name_node_map:
                raise AssertionError("Expected 'x' in name_node_map")
            name_node_map["linear"].meta["custom_annotation"] = "annotation"
            # check if we correctly annotated the target graph module
            for n in target_gm.graph.nodes:
                if n == name_node_map["linear"]:
                    if not (
                        "custom_annotation" in n.meta
                        and n.meta["custom_annotation"] == "annotation"
                    ):
                        raise AssertionError(
                            "Expected custom_annotation to be 'annotation'"
                        )
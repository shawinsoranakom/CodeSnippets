def test_matcher_with_name_node_map_function(self):
        """Testing SubgraphMatcherWithNameNodeMap with function pattern"""

        def target_graph(x, weight):
            x = x * 2
            weight = weight * 3
            conv = F.conv2d(x, weight)
            relu = F.relu(conv)
            relu2 = relu * 2
            return relu + relu2

        def pattern(x, weight):
            conv = F.conv2d(x, weight)
            relu = F.relu(conv)
            relu_mul_by_two = relu * 2
            return relu, relu_mul_by_two, {"conv": conv, "relu": relu}

        example_inputs = (
            torch.randn(1, 3, 3, 3) * 10,
            torch.randn(3, 3, 3, 3),
        )
        pattern_gm = export(
            WrapperModule(pattern), example_inputs, strict=True
        ).module()
        matcher = SubgraphMatcherWithNameNodeMap(pattern_gm)
        target_gm = export(
            WrapperModule(target_graph), example_inputs, strict=True
        ).module()
        internal_matches = matcher.match(target_gm.graph)
        for internal_match in internal_matches:
            name_node_map = internal_match.name_node_map
            if "conv" not in name_node_map:
                raise AssertionError("Expected 'conv' in name_node_map")
            if "relu" not in name_node_map:
                raise AssertionError("Expected 'relu' in name_node_map")
            name_node_map["conv"].meta["custom_annotation"] = "annotation"
            # check if we correctly annotated the target graph module
            for n in target_gm.graph.nodes:
                if n == name_node_map["conv"]:
                    if not (
                        "custom_annotation" in n.meta
                        and n.meta["custom_annotation"] == "annotation"
                    ):
                        raise AssertionError(
                            "Expected custom_annotation to be 'annotation'"
                        )
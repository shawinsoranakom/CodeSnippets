def test_group_layers(
        self,
        layer_types_str: str | None,
        sliding_window: int | None,
        expected_groups: str,
    ) -> None:
        """Test the layer grouping algorithm of the hybrid allocator."""
        # Take a config and change the layer_types attribute to the mix we want
        config = AutoConfig.from_pretrained("HuggingFaceTB/SmolLM-1.7B")

        if layer_types_str is not None:
            layer_types = [{"f": "full_attention", "s": "sliding_window"}[char] for char in layer_types_str]
        else:
            layer_types = None
            config.num_hidden_layers = len(expected_groups)

        config.layer_types = layer_types
        config.sliding_window = sliding_window

        expected_lg = {}
        for i, group in enumerate(expected_groups):
            group = int(group)
            expected_lg[group] = expected_lg.get(group, []) + [i]
        expected_layer_groups = [expected_lg[i] for i in sorted(expected_lg.keys())]

        # Test layer groups formation
        layer_groups, group_types = group_layers_by_attn_type(config)
        self.assertEqual(
            sorted(expected_layer_groups),
            sorted(layer_groups),
            f"Test failed for: {layer_types_str = }, {sliding_window = }, {expected_layer_groups = }, {layer_groups = }",
        )

        # If layer_types is provided, check that group_types matches the type of the all layers in each group
        if layer_types is not None:
            for layer_group, group_type in zip(layer_groups, group_types):
                layer_types = [config.layer_types[i] for i in layer_group]
                self.assertEqual(layer_types, [group_type] * len(layer_types))
        # If layer_types is None, all groups should be of the same type
        else:
            for group_type in group_types:
                sliding_window = getattr(config, "sliding_window", None)
                expected_group_type = "sliding_attention" if sliding_window is not None else "full_attention"
                self.assertEqual(
                    group_type,
                    expected_group_type,
                    f"Test failed for: {layer_types_str = }, {sliding_window = }, {group_types = }",
                )
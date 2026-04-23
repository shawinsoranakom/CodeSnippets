def upgrade_sublayer(
        self,
        layer_name_pattern: Union[str, List[str]],
        handle_func: Callable[[nn.Layer, str], nn.Layer],
    ) -> Dict[str, nn.Layer]:
        """use 'handle_func' to modify the sub-layer(s) specified by 'layer_name_pattern'.

        Args:
            layer_name_pattern (Union[str, List[str]]): The name of layer to be modified by 'handle_func'.
            handle_func (Callable[[nn.Layer, str], nn.Layer]): The function to modify target layer specified by 'layer_name_pattern'. The formal params are the layer(nn.Layer) and pattern(str) that is (a member of) layer_name_pattern (when layer_name_pattern is List type). And the return is the layer processed.

        Returns:
            Dict[str, nn.Layer]: The key is the pattern and corresponding value is the result returned by 'handle_func()'.

        Examples:

            from paddle import nn
            import paddleclas

            def rep_func(layer: nn.Layer, pattern: str):
                new_layer = nn.Conv2D(
                    in_channels=layer._in_channels,
                    out_channels=layer._out_channels,
                    kernel_size=5,
                    padding=2
                )
                return new_layer

            net = paddleclas.MobileNetV1()
            res = net.upgrade_sublayer(layer_name_pattern=["blocks[11].depthwise_conv.conv", "blocks[12].depthwise_conv.conv"], handle_func=rep_func)
            print(res)
            # {'blocks[11].depthwise_conv.conv': the corresponding new_layer, 'blocks[12].depthwise_conv.conv': the corresponding new_layer}
        """

        if not isinstance(layer_name_pattern, list):
            layer_name_pattern = [layer_name_pattern]

        hit_layer_pattern_list = []
        for pattern in layer_name_pattern:
            # parse pattern to find target layer and its parent
            layer_list = parse_pattern_str(pattern=pattern, parent_layer=self)
            if not layer_list:
                continue

            sub_layer_parent = layer_list[-2]["layer"] if len(layer_list) > 1 else self
            sub_layer = layer_list[-1]["layer"]
            sub_layer_name = layer_list[-1]["name"]
            sub_layer_index_list = layer_list[-1]["index_list"]

            new_sub_layer = handle_func(sub_layer, pattern)

            if sub_layer_index_list:
                if len(sub_layer_index_list) > 1:
                    sub_layer_parent = getattr(sub_layer_parent, sub_layer_name)[
                        sub_layer_index_list[0]
                    ]
                    for sub_layer_index in sub_layer_index_list[1:-1]:
                        sub_layer_parent = sub_layer_parent[sub_layer_index]
                    sub_layer_parent[sub_layer_index_list[-1]] = new_sub_layer
                else:
                    getattr(sub_layer_parent, sub_layer_name)[
                        sub_layer_index_list[0]
                    ] = new_sub_layer
            else:
                setattr(sub_layer_parent, sub_layer_name, new_sub_layer)

            hit_layer_pattern_list.append(pattern)
        return hit_layer_pattern_list
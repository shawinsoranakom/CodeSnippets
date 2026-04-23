def parse_pattern_str(
    pattern: str, parent_layer: nn.Layer
) -> Union[None, List[Dict[str, Union[nn.Layer, str, None]]]]:
    """parse the string type pattern.

    Args:
        pattern (str): The pattern to describe layer.
        parent_layer (nn.Layer): The root layer relative to the pattern.

    Returns:
        Union[None, List[Dict[str, Union[nn.Layer, str, None]]]]: None if failed. If successfully, the members are layers parsed in order:
                                                                [
                                                                    {"layer": first layer, "name": first layer's name parsed, "index": first layer's index parsed if exist},
                                                                    {"layer": second layer, "name": second layer's name parsed, "index": second layer's index parsed if exist},
                                                                    ...
                                                                ]
    """

    pattern_list = pattern.split(".")
    if not pattern_list:
        msg = f"The pattern('{pattern}') is illegal. Please check and retry."
        return None

    layer_list = []
    while len(pattern_list) > 0:
        if "[" in pattern_list[0]:
            target_layer_name = pattern_list[0].split("[")[0]
            target_layer_index_list = list(
                index.split("]")[0] for index in pattern_list[0].split("[")[1:]
            )
        else:
            target_layer_name = pattern_list[0]
            target_layer_index_list = None

        target_layer = getattr(parent_layer, target_layer_name, None)

        if target_layer is None:
            msg = f"Not found layer named('{target_layer_name}') specified in pattern('{pattern}')."
            return None

        if target_layer_index_list:
            for target_layer_index in target_layer_index_list:
                if int(target_layer_index) < 0 or int(target_layer_index) >= len(
                    target_layer
                ):
                    msg = f"Not found layer by index('{target_layer_index}') specified in pattern('{pattern}'). The index should < {len(target_layer)} and > 0."
                    return None
                target_layer = target_layer[target_layer_index]

        layer_list.append(
            {
                "layer": target_layer,
                "name": target_layer_name,
                "index_list": target_layer_index_list,
            }
        )

        pattern_list = pattern_list[1:]
        parent_layer = target_layer

    return layer_list
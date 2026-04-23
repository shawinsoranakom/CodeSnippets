def set_identity(
    parent_layer: nn.Module, layer_name: str, layer_index_list: str = None
) -> bool:
    """set the layer specified by layer_name and layer_index_list to Identity.

    Args:
        parent_layer (nn.Module): The parent layer of target layer specified by layer_name and layer_index_list.
        layer_name (str): The name of target layer to be set to Identity.
        layer_index_list (str, optional): The index of target layer to be set to Identity in parent_layer. Defaults to None.

    Returns:
        bool: True if successfully, False otherwise.
    """

    stop_after = False
    for sub_layer_name in parent_layer._sub_layers:
        if stop_after:
            parent_layer._sub_layers[sub_layer_name] = Identity()
            continue
        if sub_layer_name == layer_name:
            stop_after = True

    if layer_index_list and stop_after:
        layer_container = parent_layer._sub_layers[layer_name]
        for num, layer_index in enumerate(layer_index_list):
            stop_after = False
            for i in range(num):
                layer_container = layer_container[layer_index_list[i]]
            for sub_layer_index in layer_container._sub_layers:
                if stop_after:
                    parent_layer._sub_layers[layer_name][sub_layer_index] = Identity()
                    continue
                if layer_index == sub_layer_index:
                    stop_after = True

    return stop_after
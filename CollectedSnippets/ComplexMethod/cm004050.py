def load_adapter(full_name, value, adapter, unused_weights):
    name = full_name.split("adaptor.")[-1]
    items = name.split(".")

    if items[1].isdigit():
        layer_id = int(items[1])
    else:
        layer_id = None

    if "adaptor" not in full_name:
        if "proj_ln" in full_name:
            # has to be layer norm
            if "bias" in name:
                assert value.shape == adapter.proj_layer_norm.bias.data.shape, (
                    f"{full_name} has size {value.shape}, but {adapter.proj_layer_norm.bias.data.shape} was found."
                )
                adapter.proj_layer_norm.bias.data = value
                logger.info(f"Adapter proj layer norm bias was initialized from {full_name}.")
            if "weight" in name:
                assert value.shape == adapter.proj_layer_norm.weight.data.shape, (
                    f"{full_name} has size {value.shape}, but {adapter.proj_layer_norm.weight.data.shape} was found."
                )
                adapter.proj_layer_norm.weight.data = value
        else:
            # has to be projection layer
            if "bias" in name:
                assert value.shape == adapter.proj.bias.data.shape, (
                    f"{full_name} has size {value.shape}, but {adapter.proj.bias.data.shape} was found."
                )
                adapter.proj.bias.data = value
                logger.info(f"Adapter proj layer bias was initialized from {full_name}.")
            if "weight" in name:
                assert value.shape == adapter.proj.weight.data.shape, (
                    f"{full_name} has size {value.shape}, but {adapter.proj.weight.data.shape} was found."
                )
                adapter.proj.weight.data = value
                logger.info(f"Adapter proj layer weight was initialized from {full_name}.")
    elif isinstance(layer_id, int):
        if "bias" in name:
            assert value.shape == adapter.layers[layer_id].conv.bias.data.shape, (
                f"{full_name} has size {value.shape}, but {adapter.layers[layer_id].conv.bias.data.shape} was found."
            )
            adapter.layers[layer_id].conv.bias.data = value
            logger.info(f"Adapter layer {layer_id} bias was initialized from {full_name}.")
        elif "weight" in name:
            assert value.shape == adapter.layers[layer_id].conv.weight.data.shape, (
                f"{full_name} has size {value.shape}, but {adapter.layers[layer_id].conv.weight.data.shape} was found."
            )
            adapter.layers[layer_id].conv.weight.data = value
            logger.info(f"Adapter layer {layer_id} bias was initialized from {full_name}.")
    else:
        unused_weights.append(full_name)
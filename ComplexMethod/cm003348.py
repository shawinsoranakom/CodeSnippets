def merge_weights(state_dict):
    new_state_dict = copy.deepcopy(state_dict)

    # Merge the weights
    for weights_to_merge, new_weight_name in WEIGHTS_TO_MERGE_MAPPING:
        for weight in weights_to_merge:
            assert weight in state_dict, f"Weight {weight} is missing in the state dict"
            if new_weight_name not in new_state_dict:
                new_state_dict[new_weight_name] = [state_dict[weight]]
            else:
                new_state_dict[new_weight_name].append(state_dict[weight])
        new_state_dict[new_weight_name] = torch.cat(new_state_dict[new_weight_name], dim=0)

    # Remove the weights that were merged
    for weights_to_merge, new_weight_name in WEIGHTS_TO_MERGE_MAPPING:
        for weight in weights_to_merge:
            if weight in new_state_dict and weight != new_weight_name:
                new_state_dict.pop(weight)

    return new_state_dict
def merge_weights(state_dict, new_state_dict):
    old_weight_names = set(state_dict.keys())

    # Merge the weights
    for weights_to_merge, new_weight_name in WEIGHTS_TO_MERGE_MAPPING:
        for weight_to_merge in weights_to_merge:
            print(weight_to_merge)
            assert weight_to_merge in state_dict, f"Weight {weight_to_merge} is missing in the state dict"

            weight = state_dict.pop(weight_to_merge)
            if new_weight_name not in new_state_dict:
                new_state_dict[new_weight_name] = [weight]
            else:
                new_state_dict[new_weight_name].append(weight)

            old_weight_names.remove(weight_to_merge)

        new_state_dict[new_weight_name] = torch.cat(new_state_dict[new_weight_name], dim=0)

    # Remove the weights that were merged
    for weights_to_merge, new_weight_name in WEIGHTS_TO_MERGE_MAPPING:
        for weight in weights_to_merge:
            if weight in new_state_dict and weight != new_weight_name:
                new_state_dict.pop(weight)

    return new_state_dict
def convert_old_keys_to_new_keys(original_state_dict: dict[str, torch.Tensor]) -> dict[str, torch.Tensor]:
    converted_checkpoint: dict[str, torch.Tensor] = {}

    for old_key, value in original_state_dict.items():
        if old_key.startswith("encoder."):
            layer_key = old_key[len("encoder.") :]
            for pattern, path_parts in MAPPING_ACOUSTIC_ENCODER.items():
                pattern_match = re.match(pattern, layer_key)
                if pattern_match is None:
                    continue

                digit_strings = [g for g in pattern_match.groups() if g is not None]
                digit_indices = [int(ds) for ds in digit_strings]
                remainder = layer_key[pattern_match.end() :]

                if len(path_parts) == 1:
                    mapped_subkey = f"{path_parts[0]}{remainder}"
                elif len(path_parts) == 2:
                    encoder_layer = digit_indices[0] - 1
                    mapped_subkey = f"{path_parts[0]}.{encoder_layer}.{path_parts[1]}{remainder}"
                else:
                    encoder_layer, unit_idx = digit_indices
                    mapped_subkey = (
                        f"{path_parts[0]}.{encoder_layer - 1}.{path_parts[1]}{unit_idx + 1}.{path_parts[2]}{remainder}"
                    )

                new_key = f"acoustic_encoder.{_rewrite_weight_norm(mapped_subkey)}"
                converted_checkpoint[new_key] = value
                break

        elif old_key.startswith("decoder_2."):
            layer_key = old_key[len("decoder_2.") :]

            for pattern, path_parts in MAPPING_ACOUSTIC_DECODER.items():
                pattern_match = re.match(pattern, layer_key)
                if pattern_match is None:
                    continue
                digit_strings = [g for g in pattern_match.groups() if g is not None]
                digit_indices = [int(ds) for ds in digit_strings]
                remainder = layer_key[pattern_match.end() :]

                if len(path_parts) == 1:
                    mapped_subkey = f"{path_parts[0]}{remainder}"
                elif len(path_parts) == 2:
                    decoder_layer = digit_indices[0] - 1
                    mapped_subkey = f"{path_parts[0]}.{decoder_layer}.{path_parts[1]}{remainder}"
                else:
                    decoder_layer, unit_idx = digit_indices
                    mapped_subkey = (
                        f"{path_parts[0]}.{decoder_layer - 1}.{path_parts[1]}{unit_idx - 1}.{path_parts[2]}{remainder}"
                    )
                new_key = f"acoustic_decoder.{_rewrite_weight_norm(mapped_subkey)}"
                converted_checkpoint[new_key] = value
                break

        elif old_key.startswith("encoder_semantic."):
            semantic_key = old_key[len("encoder_semantic.") :]
            for old, new in MAPPING_SEMANTIC_ENCODER.items():
                semantic_key = semantic_key.replace(old, new)
            converted_checkpoint[f"encoder_semantic.{semantic_key}"] = value

        elif old_key.startswith("decoder_semantic."):
            semantic_key = old_key[len("decoder_semantic.") :]
            for old, new in MAPPING_SEMANTIC_DECODER.items():
                semantic_key = semantic_key.replace(old, new)
            converted_checkpoint[f"decoder_semantic.{semantic_key}"] = value

        elif old_key.startswith("semantic_model."):
            converted_checkpoint[old_key] = value

        elif old_key.startswith("fc_prior."):
            converted_checkpoint[f"fc.{old_key[len('fc_prior.') :]}"] = value

        elif old_key.startswith("fc_post1."):
            converted_checkpoint[f"fc1.{old_key[len('fc_post1.') :]}"] = value

        elif old_key.startswith("fc_post2."):
            converted_checkpoint[f"fc2.{old_key[len('fc_post2.') :]}"] = value

        elif old_key.startswith("quantizer.vq.layers"):
            new_key = old_key
            for old_sub, new_sub in MAPPING_QUANTIZER.items():
                new_key = new_key.replace(old_sub, new_sub)
            converted_checkpoint[new_key] = value

    return converted_checkpoint
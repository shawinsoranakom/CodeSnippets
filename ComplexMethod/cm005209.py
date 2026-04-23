def convert_audio_encoder_weights(
    config: Gemma3nAudioConfig,
    path: str,
    param: str,
    weights: np.ndarray,
) -> Iterable[tuple[str, np.ndarray]]:
    converted_paths: list[str] = []
    converted_weights: list[Any] = []

    if path.startswith(_AUDIO_ENCODER_CONFORMER):
        assert weights.shape[0] == config.conf_num_hidden_layers

        for i, matrix in enumerate(weights):
            if "fflayer_end" in path:
                base = f"conformer.{i}.ffw_layer_end"

                if path.endswith("ffn_layer1"):
                    converted_paths.append(f"{base}.ffw_layer_1.weight")
                    converted_weights.append(matrix.transpose())
                elif path.endswith("ffn_layer2"):
                    converted_paths.append(f"{base}.ffw_layer_2.weight")
                    converted_weights.append(matrix.transpose())
                elif path.endswith("post_layer_norm"):
                    converted_paths.append(f"{base}.post_layer_norm.weight")
                    converted_weights.append(matrix)
                elif path.endswith("pre_layer_norm"):
                    converted_paths.append(f"{base}.pre_layer_norm.weight")
                    converted_weights.append(matrix)
            elif "fflayer_start" in path:
                base = f"conformer.{i}.ffw_layer_start"

                if path.endswith("ffn_layer1"):
                    converted_paths.append(f"{base}.ffw_layer_1.weight")
                    converted_weights.append(matrix.transpose())
                elif path.endswith("ffn_layer2"):
                    converted_paths.append(f"{base}.ffw_layer_2.weight")
                    converted_weights.append(matrix.transpose())
                elif path.endswith("post_layer_norm"):
                    converted_paths.append(f"{base}.post_layer_norm.weight")
                    converted_weights.append(matrix)
                elif path.endswith("pre_layer_norm"):
                    converted_paths.append(f"{base}.pre_layer_norm.weight")
                    converted_weights.append(matrix)
            elif path.endswith("final_ln"):
                converted_paths.append(f"conformer.{i}.norm.weight")
                converted_weights.append(matrix)
            elif "lconv" in path:
                base = f"conformer.{i}.lconv1d"

                if path.endswith("conv_norm"):
                    converted_paths.append(f"{base}.conv_norm.weight")
                    converted_weights.append(matrix)
                elif path.endswith("depthwise_conv1d"):
                    converted_paths.append(f"{base}.depthwise_conv1d.weight")
                    converted_weights.append(matrix.transpose())
                elif path.endswith("linear_end"):
                    converted_paths.append(f"{base}.linear_end.weight")
                    converted_weights.append(matrix.transpose())
                elif path.endswith("linear_start"):
                    converted_paths.append(f"{base}.linear_start.weight")
                    converted_weights.append(matrix.transpose())
                elif path.endswith("ln"):
                    converted_paths.append(f"{base}.pre_layer_norm.weight")
                    converted_weights.append(matrix)
            elif "trans_atten" in path:
                base = f"conformer.{i}.attention"

                if param == "per_dim_scale":
                    converted_paths.append(f"{base}.attn.per_dim_scale")
                    converted_weights.append(matrix)

                if path.endswith("query_key_value_projection"):
                    converted_paths.extend(
                        [f"{base}.attn.q_proj.weight", f"{base}.attn.k_proj.weight", f"{base}.attn.v_proj.weight"]
                    )
                    converted_weights.extend(
                        [
                            m.reshape(config.hidden_size, config.hidden_size).transpose()
                            for m in matrix.transpose(1, 0, 2, 3)
                        ]
                    )
                elif path.endswith("pos_proj"):
                    converted_paths.append(f"{base}.attn.relative_position_embedding.pos_proj.weight")
                    converted_weights.append(matrix.reshape(config.hidden_size, config.hidden_size).transpose())
                elif path.endswith("post"):
                    converted_paths.append(f"{base}.post.weight")
                    converted_weights.append(matrix.transpose(2, 0, 1).reshape(config.hidden_size, config.hidden_size))
                elif path.endswith("post_norm"):
                    converted_paths.append(f"{base}.post_norm.weight")
                    converted_weights.append(matrix)
                elif path.endswith("pre_norm"):
                    converted_paths.append(f"{base}.pre_attn_norm.weight")
                    converted_weights.append(matrix)
    elif path.startswith(_AUDIO_ENCODER_SSCP):
        if path.endswith("input_proj"):
            converted_paths.append("subsample_conv_projection.input_proj_linear.weight")
            converted_weights.append(
                weights.transpose(2, 0, 1).reshape(config.hidden_size, config.sscp_conv_channel_size[1] ** 2)
            )
        elif "norm_" in path:
            index = int(path[-1])
            converted_paths.append(f"subsample_conv_projection.conv_{index}.norm.weight")
            converted_weights.append(weights)
        elif "subsampling_" in path:
            index = int(path[-1])
            converted_paths.append(f"subsample_conv_projection.conv_{index}.conv.weight")
            converted_weights.append(weights.transpose(3, 2, 0, 1))

    if (cpl := len(converted_paths)) != (cwl := len(converted_weights)):
        raise ValueError(
            "The `converted_paths` and `converted_weights` should be the same "
            f"length. Got {cpl} and {cwl}, respectively, for {path}."
        )

    return zip(converted_paths, converted_weights)
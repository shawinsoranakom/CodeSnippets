def convert_audio_encoder_weights(
    config,  # Gemma4AudioConfig
    path: str,
    param: str,
    weights: np.ndarray,
) -> Iterable[tuple[str, np.ndarray]]:
    converted_paths: list[str] = []
    converted_weights: list[Any] = []

    # The conformer uses its own internal dimension (1024 by default via conf_hidden_size).
    # Since we now use the default hidden_size=1024 (same as conf_hidden_size),
    # we use config.conf_hidden_size for reshaping conformer weights.

    if path.startswith(_AUDIO_ENCODER_CONFORMER):
        assert weights.shape[0] == config.num_hidden_layers

        for i, matrix in enumerate(weights):
            if "fflayer_end" in path:
                base = f"layers.{i}.feed_forward2"

                if path.endswith("ffn_layer1/ClippedEinsum_0"):
                    converted_paths.append(f"{base}.ffw_layer_1.{param.removeprefix('clip_')}")
                    converted_weights.append(matrix)
                elif path.endswith("ffn_layer2/ClippedEinsum_0"):
                    converted_paths.append(f"{base}.ffw_layer_2.{param.removeprefix('clip_')}")
                    converted_weights.append(matrix)
                elif path.endswith("ffn_layer1"):
                    converted_paths.append(f"{base}.ffw_layer_1.linear.weight")
                    converted_weights.append(matrix.transpose())
                elif path.endswith("ffn_layer2"):
                    converted_paths.append(f"{base}.ffw_layer_2.linear.weight")
                    converted_weights.append(matrix.transpose())
                elif path.endswith("post_layer_norm"):
                    converted_paths.append(f"{base}.post_layer_norm.weight")
                    converted_weights.append(matrix)
                elif path.endswith("pre_layer_norm"):
                    converted_paths.append(f"{base}.pre_layer_norm.weight")
                    converted_weights.append(matrix)
            elif "fflayer_start" in path:
                base = f"layers.{i}.feed_forward1"

                if path.endswith("ffn_layer1/ClippedEinsum_0"):
                    converted_paths.append(f"{base}.ffw_layer_1.{param.removeprefix('clip_')}")
                    converted_weights.append(matrix)
                elif path.endswith("ffn_layer2/ClippedEinsum_0"):
                    converted_paths.append(f"{base}.ffw_layer_2.{param.removeprefix('clip_')}")
                    converted_weights.append(matrix)
                elif path.endswith("ffn_layer1"):
                    converted_paths.append(f"{base}.ffw_layer_1.linear.weight")
                    converted_weights.append(matrix.transpose())
                elif path.endswith("ffn_layer2"):
                    converted_paths.append(f"{base}.ffw_layer_2.linear.weight")
                    converted_weights.append(matrix.transpose())
                elif path.endswith("post_layer_norm"):
                    converted_paths.append(f"{base}.post_layer_norm.weight")
                    converted_weights.append(matrix)
                elif path.endswith("pre_layer_norm"):
                    converted_paths.append(f"{base}.pre_layer_norm.weight")
                    converted_weights.append(matrix)
            elif path.endswith("final_ln"):
                converted_paths.append(f"layers.{i}.norm_out.weight")
                converted_weights.append(matrix)
            elif "lconv" in path:
                base = f"layers.{i}.lconv1d"

                if path.endswith("linear_start/ClippedEinsum_0"):
                    converted_paths.append(f"{base}.linear_start.{param.removeprefix('clip_')}")
                    converted_weights.append(matrix)
                elif path.endswith("linear_end/ClippedEinsum_0"):
                    converted_paths.append(f"{base}.linear_end.{param.removeprefix('clip_')}")
                    converted_weights.append(matrix)
                elif path.endswith("conv_norm"):
                    converted_paths.append(f"{base}.conv_norm.weight")
                    converted_weights.append(matrix)
                elif path.endswith("depthwise_conv1d"):
                    converted_paths.append(f"{base}.depthwise_conv1d.weight")
                    converted_weights.append(matrix.transpose())
                elif path.endswith("linear_end"):
                    converted_paths.append(f"{base}.linear_end.linear.weight")
                    converted_weights.append(matrix.transpose())
                elif path.endswith("linear_start"):
                    converted_paths.append(f"{base}.linear_start.linear.weight")
                    converted_weights.append(matrix.transpose())
                elif path.endswith("ln"):
                    converted_paths.append(f"{base}.pre_layer_norm.weight")
                    converted_weights.append(matrix)
            elif "trans_atten" in path:
                base = f"layers.{i}"

                if param == "per_dim_scale":
                    converted_paths.append(f"{base}.self_attn.per_dim_scale")
                    converted_weights.append(matrix)

                if path.endswith("query_key_value_projection/ClippedEinsum_0"):
                    converted_paths.append(f"{base}.self_attn.q_proj.{param.removeprefix('clip_')}")
                    converted_weights.append(matrix)
                    converted_paths.append(f"{base}.self_attn.k_proj.{param.removeprefix('clip_')}")
                    converted_weights.append(matrix)
                    converted_paths.append(f"{base}.self_attn.v_proj.{param.removeprefix('clip_')}")
                    converted_weights.append(matrix)
                elif path.endswith("post/ClippedEinsum_0"):
                    converted_paths.append(f"{base}.self_attn.post.{param.removeprefix('clip_')}")
                    converted_weights.append(matrix)

                if path.endswith("query_key_value_projection"):
                    converted_paths.extend(
                        [
                            f"{base}.self_attn.q_proj.linear.weight",
                            f"{base}.self_attn.k_proj.linear.weight",
                            f"{base}.self_attn.v_proj.linear.weight",
                        ]
                    )
                    converted_weights.extend(
                        [
                            m.reshape(config.hidden_size, config.hidden_size).transpose()
                            for m in matrix.transpose(1, 0, 2, 3)
                        ]
                    )
                elif path.endswith("pos_proj"):
                    converted_paths.append(f"{base}.self_attn.relative_k_proj.weight")
                    converted_weights.append(matrix.reshape(config.hidden_size, config.hidden_size).transpose())
                elif path.endswith("post"):
                    converted_paths.append(f"{base}.self_attn.post.linear.weight")
                    converted_weights.append(matrix.transpose(2, 0, 1).reshape(config.hidden_size, config.hidden_size))
                elif path.endswith("post_norm"):
                    converted_paths.append(f"{base}.norm_post_attn.weight")
                    converted_weights.append(matrix)
                elif path.endswith("pre_norm"):
                    converted_paths.append(f"{base}.norm_pre_attn.weight")
                    converted_weights.append(matrix)
    elif path.startswith(_AUDIO_ENCODER_SSCP):
        if path.endswith("input_proj"):
            converted_paths.append("subsample_conv_projection.input_proj_linear.weight")
            converted_weights.append(
                weights.transpose(2, 0, 1).reshape(config.hidden_size, config.subsampling_conv_channels[1] ** 2)
            )
        elif "norm_" in path:
            index = int(path[-1])
            converted_paths.append(f"subsample_conv_projection.layer{index}.norm.weight")
            converted_weights.append(weights)
        elif "subsampling_" in path:
            index = int(path[-1])
            converted_paths.append(f"subsample_conv_projection.layer{index}.conv.weight")
            converted_weights.append(weights.transpose(3, 2, 0, 1))

    elif path.endswith("output_projection"):
        if param == "kernel":
            converted_paths.append("output_proj.weight")
            converted_weights.append(weights.transpose())
        elif param == "bias":
            converted_paths.append("output_proj.bias")
            converted_weights.append(weights)

    if (cpl := len(converted_paths)) != (cwl := len(converted_weights)):
        raise ValueError(
            "The `converted_paths` and `converted_weights` should be the same "
            f"length. Got {cpl} and {cwl}, respectively, for {path}."
        )

    return zip(converted_paths, converted_weights)
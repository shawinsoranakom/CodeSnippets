def maybe_log_flex_attention_results(
        name: str, input_nodes: list[ir.IRNode], timings: dict[ChoiceCaller, float]
    ) -> None:
        flex_attention_filename = get_flex_attention_log_filename()
        # Support both flex_attention and flex_decoding
        if not flex_attention_filename or (
            "flex_attention" not in name and "flex_decoding" not in name
        ):
            return

        if len(input_nodes) < 3:
            return

        query_size = input_nodes[0].get_size()
        key_size = input_nodes[1].get_size()
        value_size = input_nodes[2].get_size()

        # Handle both 4D (forward/backward) and 5D (decode) tensor formats
        # 4D: [B, H, seq_len, head_dim]
        # 5D: [B, H, 1, 1, head_dim] (decode mode has extra dimension)
        if len(query_size) == 5:
            # Decode mode with 5D tensors
            B = query_size[0]
            Hq = query_size[1]
            # query_size[2] and query_size[3] are both 1 for decode
            seq_len_q = query_size[2]  # This will be 1
            qk_head_dim = query_size[4]  # Head dim is at index 4 for 5D
            Hkv = key_size[1]
            seq_len_kv = key_size[2]
            v_head_dim = value_size[4] if len(value_size) == 5 else value_size[3]
        else:
            # Forward/backward mode with 4D tensors
            B = query_size[0]
            Hq = query_size[1]
            seq_len_q = query_size[2]
            qk_head_dim = query_size[3]
            Hkv = key_size[1]
            seq_len_kv = key_size[2]
            v_head_dim = value_size[3]

        kernel_type = (
            "backward"
            if "backward" in name
            else ("decode" if "decoding" in name else "forward")
        )

        # Create shape info dictionary
        shape_info = {
            "kernel_type": kernel_type,
            "B": int(B),
            "Hq": int(Hq),
            "Hkv": int(Hkv),
            "seq_len_q": int(seq_len_q),
            "seq_len_kv": int(seq_len_kv),
            "qk_head_dim": int(qk_head_dim),
            "v_head_dim": int(v_head_dim),
        }

        sorted_choices = sorted(timings, key=timings.__getitem__)

        # Include shape info in each choice
        choices_with_shapes = []
        for choice in sorted_choices:
            choice_info = AlgorithmSelectorCache.get_flex_attention_choice_info(
                choice, timings
            )
            # Merge shape info with choice info
            choice_info.update(shape_info)
            choices_with_shapes.append(choice_info)

        out_dict = {
            "query_shape": str(query_size),
            "key_shape": str(key_size),
            "value_shape": str(value_size),
            "kernel_type": kernel_type,
            "choices": choices_with_shapes,
        }
        append_to_log(flex_attention_filename, out_dict)
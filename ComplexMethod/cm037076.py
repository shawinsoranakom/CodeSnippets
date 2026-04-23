def _remap_mistral_sliding_window(config: dict) -> dict:
    # Remap sliding_window (list) -> layer_types (list) + sliding window (int)
    # for HF compatibility
    # Mistral configs may define sliding_window as list[int]. Convert it
    # to int and add the layer_types list[str] to make it HF compatible
    if sliding_window := config.get("sliding_window"):
        if isinstance(sliding_window, list):
            pattern_repeats = config["num_hidden_layers"] // len(sliding_window)
            layer_types = sliding_window * pattern_repeats
            config["layer_types"] = [
                "full_attention" if layer_type is None else "sliding_attention"
                for layer_type in layer_types
            ]
            assert len(set(sliding_window) - {None}) <= 1, sliding_window
            config["sliding_window"] = next(filter(None, sliding_window), None)
        elif isinstance(sliding_window, int) and config.get("layer_types") is None:
            config["layer_types"] = ["sliding_attention"] * config["num_hidden_layers"]
        else:
            raise ValueError(f"Unsupported sliding_window type: {sliding_window}")

    return config
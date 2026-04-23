def resolve_visual_encoder_outputs(
    encoder_outputs: torch.Tensor | list[torch.Tensor],
    post_layer_norm: torch.nn.LayerNorm | None,
    *,
    select_layers: list[int] | None = None,
    max_possible_layers: int | None = None,
    last_hs_proc: Callable[[torch.Tensor], torch.Tensor] | None = None,
    feature_select_strategy: VisionFeatureSelectStrategy | None = None,
) -> torch.Tensor:
    """Given the outputs a visual encoder module that may correspond to the
    output of the last layer, or a list of hidden states to be stacked,
    handle post normalization and resolve it into a single output tensor.

    Args:
        encoder_outputs: Output of encoder's last layer or all hidden states.
        post_layer_norm: Post norm to apply to the output of the encoder.
        select_layers: Optional layer indices to grab from the encoder
            outputs; if provided, encoder outputs must be a list.
        max_possible_layers: Total layers in the fully loaded visual encoder.
        last_hs_proc: Optional callable to be applied to the last layer if it
            is used, e.g., pooling head for Siglip. This is done prior to
            feature selection and layer normalization. If select_layers are
            provided, the output of last_hs_proc must be able to be
            concatenated with the other select_layers along the last dimension.
        feature_select_strategy: Defines how to select the hidden states
            from each layer.
    """
    if select_layers is None:
        if not isinstance(encoder_outputs, torch.Tensor):
            raise ValueError(
                "Expected only a single encoder output when "
                "`select_layers` is not provided"
            )

        # Preprocess the encoder outputs as needed, e.g., map head
        # and layer norm for siglip, which runs before feature selection
        if last_hs_proc is not None:
            encoder_outputs = last_hs_proc(encoder_outputs)

        if feature_select_strategy is not None:
            select_features = _get_vision_feature_selector(feature_select_strategy)
            encoder_outputs = select_features(encoder_outputs)

        if post_layer_norm is not None:
            return post_layer_norm(encoder_outputs)

        return encoder_outputs

    if max_possible_layers is None:
        raise ValueError(
            "`max_possible_layers` must be provided alongside `select_layers`"
        )

    # Get the hidden states corresponding to the layer indices.
    # Negative values are relative to the full visual encoder,
    # so offset them depending on how many layers were loaded.
    # NOTE: this assumes that encoder_outputs is a list containing
    # the inputs to the visual encoder, followed by the hidden states
    # of each layer.
    num_loaded_layers = len(encoder_outputs) - 1
    offset = max_possible_layers - num_loaded_layers
    hs_pool = [
        encoder_outputs[layer_idx]
        if layer_idx >= 0
        else encoder_outputs[layer_idx + offset]
        for layer_idx in select_layers
    ]

    uses_last_layer = select_layers[-1] in (max_possible_layers - 1, -1)
    if last_hs_proc is not None and uses_last_layer:
        hs_pool[-1] = last_hs_proc(hs_pool[-1])

    if feature_select_strategy is not None:
        select_features = _get_vision_feature_selector(feature_select_strategy)
        hs_pool = [select_features(hs) for hs in hs_pool]

    # Apply post-norm on the final hidden state if we are using it
    if post_layer_norm is not None and uses_last_layer:
        hs_pool[-1] = post_layer_norm(hs_pool[-1])

    return torch.cat(hs_pool, dim=-1)
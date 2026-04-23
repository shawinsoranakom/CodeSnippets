def _compute_yarn_parameters(
    config: "PreTrainedConfig",
    device: Optional["torch.device"] = None,
    seq_len: int | None = None,
    layer_type: str | None = None,
) -> tuple["torch.Tensor", float]:
    """
    Computes the inverse frequencies with NTK scaling. Please refer to the
    [original paper](https://huggingface.co/papers/2309.00071)

    Args:
        config ([`~transformers."PreTrainedConfig"`]):
            The model configuration. This function assumes that the config will provide at least the following
            properties:

            *   rope_theta (`float`, *optional*): The base wavelength from which the inverse frequencies will be derived. Defaults to `config.default_theta` if omitted.
            *   hidden_size (`int`): The numerator when deriving a head_dim, if not provided directly.
            *   num_attention_heads (`int`): The denominator when deriving a head_dim, if not provided directly.
            *   max_position_embeddings (`int`): The maximum length of the positional embeddings.
            *   rope_parameters (`dict[str, float | int]`): The standard RoPE scaling parameters, from which the following
                keys will be accessed:
                *   `attention_factor` (`float`, *optional*): The scaling factor to be applied to the computed cos/sin.
                    If None, the value is inferred from `factor`, `mscale`, and `mscale_all_dim` as available.
                *   `beta_fast` (`float`, *optional*, defaults to 32): Parameter to set the boundary for extrapolation
                    (only) in the linear ramp function.
                *   `beta_slow` (`float`, *optional*, defaults to 1): Parameter to set the boundary for interpolation
                    (only) in the linear ramp function.
                *   `factor` (`float`, *optional*): The scaling factor applied when interpolating the position IDs to
                    extend the possible context length. Additionally, if `attention_factor` is None, the log of this
                    value is used to compute a value for `attention_factor`, possibly in conjunciton with `mscale` and
                    `mscale_all_dim`, if provided.
                *   `mscale` (`float`, *optional*): If `attention_factor` is None and both `mscale` and
                    `mscale_all_dim` are provided, `mscale` acts scalar augmenting `log(factor)` when computing the
                    numerator for the inferred value of `attention_factor`. If not provided, `attention_factor` will be
                    calculated based on `factor` only.
                *   `mscale_all_dim` (`float`, *optional*): If `attention_factor` is None and both `mscale` and
                    `mscale_all_dim` are provided, `mscale_all_dim` acts scalar augmenting `log(factor)` when computing
                    the denominator for the inferred value of `attention_factor`. If not provided, `attention_factor`
                    will be calculated based on `factor` only.
                *   `original_max_position_embeddings` (`int`): The original max position embeddings used during pretraining.
                *   `truncate` (`bool`, *optional*): Whether to truncate the correction range.

            Additionally, this function will make use of the following properties if they are found in the config:

            *   head_dim (`int`, *optional*): The size of the key-value heads in the model. If None, this value will be
                derived as hidden_size // num_attention_heads.
            *   partial_rotary_factor (`float`, *optional*, defaults to 1.0): If less than 1.0, inverse frequencies
                will be returned for the first fraction of the head_dim.
        device (`torch.device`):
            The device to use for initialization of the inverse frequencies.
        seq_len (`int`, *optional*):
            The current sequence length. Unused for this type of RoPE.

    Returns:
        Tuple of (`torch.Tensor`, `float`), containing the inverse frequencies for the RoPE embeddings and the
        post-processing scaling factor applied to the computed cos/sin.
    """
    # For backward compatibility standardize the `rope_parameters_dict` if it uses old format
    config.standardize_rope_params()
    rope_parameters_dict = config.rope_parameters[layer_type] if layer_type is not None else config.rope_parameters

    base = rope_parameters_dict["rope_theta"]
    partial_rotary_factor = rope_parameters_dict.get("partial_rotary_factor", 1.0)
    head_dim = getattr(config, "head_dim", config.hidden_size // config.num_attention_heads)
    dim = int(head_dim * partial_rotary_factor)

    factor = rope_parameters_dict["factor"]
    attention_factor = rope_parameters_dict.get("attention_factor")
    mscale = rope_parameters_dict.get("mscale")
    mscale_all_dim = rope_parameters_dict.get("mscale_all_dim")
    original_max_position_embeddings = rope_parameters_dict["original_max_position_embeddings"]

    # NOTE: DeekSeek-V3 (and potentially other models) have `original_max_position_embeddings` field
    # containing the pretrained value. They use the ratio between `max_position_embeddings` and this value
    # to compute the default attention scaling factor, instead of using `factor`.
    if factor is None:
        factor = config.max_position_embeddings / original_max_position_embeddings

    def get_mscale(scale, mscale=1):
        if scale <= 1:
            return 1.0
        return 0.1 * mscale * math.log(scale) + 1.0

    # Sets the attention factor as suggested in the paper
    if attention_factor is None:
        if mscale and mscale_all_dim:
            attention_factor = float(get_mscale(factor, mscale) / get_mscale(factor, mscale_all_dim))
        else:
            attention_factor = get_mscale(factor)

    # Optional config options
    # beta_fast/beta_slow: as suggested in the paper, default to 32/1 (correspondingly)
    beta_fast = rope_parameters_dict.get("beta_fast") or 32
    beta_slow = rope_parameters_dict.get("beta_slow") or 1

    # Compute the inverse frequencies
    def find_correction_dim(num_rotations, dim, base, max_position_embeddings):
        """Inverse dimension formula to find the dimension based on the number of rotations"""
        return (dim * math.log(max_position_embeddings / (num_rotations * 2 * math.pi))) / (2 * math.log(base))

    def find_correction_range(low_rot, high_rot, dim, base, max_position_embeddings, truncate):
        """Find dimension range bounds based on rotations"""
        low = find_correction_dim(low_rot, dim, base, max_position_embeddings)
        high = find_correction_dim(high_rot, dim, base, max_position_embeddings)
        if truncate:
            low = math.floor(low)
            high = math.ceil(high)
        return max(low, 0), min(high, dim - 1)

    def linear_ramp_factor(min, max, dim):
        if min == max:
            max += 0.001  # Prevent singularity

        linear_func = (torch.arange(dim, dtype=torch.float32) - min) / (max - min)
        ramp_func = torch.clamp(linear_func, 0, 1)
        return ramp_func

    # Note on variable naming: "interpolation" comes from the original technique, where we interpolate the position IDs
    # to expand the possible context length. In other words, interpolation = apply scaling factor.
    pos_freqs = base ** (torch.arange(0, dim, 2).to(device=device, dtype=torch.float) / dim)
    inv_freq_extrapolation = 1.0 / pos_freqs
    inv_freq_interpolation = 1.0 / (factor * pos_freqs)

    truncate = config.rope_parameters.get("truncate", True)
    low, high = find_correction_range(beta_fast, beta_slow, dim, base, original_max_position_embeddings, truncate)

    # Get n-dimensional rotational scaling corrected for extrapolation
    inv_freq_extrapolation_factor = 1 - linear_ramp_factor(low, high, dim // 2).to(device=device, dtype=torch.float)
    inv_freq = (
        inv_freq_interpolation * (1 - inv_freq_extrapolation_factor)
        + inv_freq_extrapolation * inv_freq_extrapolation_factor
    )
    return inv_freq, attention_factor
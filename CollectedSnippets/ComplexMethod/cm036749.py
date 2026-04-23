def test_rope_module_cache(default_vllm_config):
    MAX_POSITIONS = [123, 1234]
    ROPE_THETAS = [10000, 1000000]
    ROPE_PARAMETERS = (
        {"rope_type": "default"},
        {"rope_type": "linear", "factor": (1,)},
        {"rope_type": "dynamic", "factor": 1},
    )
    settings = (
        HEAD_SIZES,
        ROTARY_DIMS,
        MAX_POSITIONS,
        ROPE_THETAS,
        IS_NEOX_STYLE,
        ROPE_PARAMETERS,
        DTYPES,
    )
    rope_setting_id_map: dict[str, int] = {}
    for setting in product(*settings):
        (
            head_size,
            rotary_dim,
            max_position,
            rope_theta,
            is_neox_style,
            rope_parameters,
            dtype,
        ) = setting
        if rotary_dim is None:
            rotary_dim = head_size
        rope_parameters["rope_theta"] = rope_theta
        rope_parameters["partial_rotary_factor"] = rotary_dim / head_size
        rope = get_rope(
            head_size,
            max_position,
            is_neox_style,
            rope_parameters,
            dtype,
        )
        # different settings cannot share the same rope module
        assert id(rope) not in rope_setting_id_map.values()
        assert all(x.dtype == dtype for x in rope.buffers())
        assert all(x.dtype == dtype for x in rope.parameters())
        rope_setting_id_map[str(setting)] = id(rope)

    for setting in product(*settings):
        (
            head_size,
            rotary_dim,
            max_position,
            rope_theta,
            is_neox_style,
            rope_parameters,
            dtype,
        ) = setting
        if rotary_dim is None:
            rotary_dim = head_size
        rope_parameters["rope_theta"] = rope_theta
        rope_parameters["partial_rotary_factor"] = rotary_dim / head_size
        rope = get_rope(
            head_size,
            max_position,
            is_neox_style,
            rope_parameters,
            dtype,
        )
        # check if cache take effect
        assert id(rope) == rope_setting_id_map[str(setting)]
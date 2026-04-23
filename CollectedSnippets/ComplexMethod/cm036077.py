def _assert_has_all_expected(keys: set[str]) -> None:
    # text
    for k in ("text_pair", "text_target", "text_pair_target"):
        assert k in keys
    # image
    for k in ("do_convert_rgb", "do_resize"):
        assert k in keys
    # audio
    for k in (
        "fps",
        "do_sample_frames",
        "input_data_format",
        "default_to_square",
    ):
        assert k in keys
    # audio
    for k in ("padding", "return_attention_mask"):
        assert k in keys
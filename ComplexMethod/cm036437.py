def test_compilation_mode_string_values(parser):
    """Test that -cc.mode accepts both integer and string mode values."""
    args = parser.parse_args(["-cc.mode", "0"])
    assert args.compilation_config == {"mode": 0}

    args = parser.parse_args(["-O3"])
    assert args.optimization_level == 3

    args = parser.parse_args(["-cc.mode=NONE"])
    assert args.compilation_config == {"mode": "NONE"}

    args = parser.parse_args(["-cc.mode", "STOCK_TORCH_COMPILE"])
    assert args.compilation_config == {"mode": "STOCK_TORCH_COMPILE"}

    args = parser.parse_args(["-cc.mode=DYNAMO_TRACE_ONCE"])
    assert args.compilation_config == {"mode": "DYNAMO_TRACE_ONCE"}

    args = parser.parse_args(["-cc.mode", "VLLM_COMPILE"])
    assert args.compilation_config == {"mode": "VLLM_COMPILE"}

    args = parser.parse_args(["-cc.mode=none"])
    assert args.compilation_config == {"mode": "none"}

    args = parser.parse_args(["-cc.mode=vllm_compile"])
    assert args.compilation_config == {"mode": "vllm_compile"}
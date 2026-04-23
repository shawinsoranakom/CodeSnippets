def test_duplicate_dict_args(caplog_vllm, parser):
    args = [
        "--model-name=something.something",
        "--hf-overrides.key1",
        "val1",
        "--hf-overrides.key1",
        "val2",
        "-O1",
        "-cc.mode",
        "2",
        "-O3",
    ]

    parsed_args = parser.parse_args(args)
    # Should be the last value
    assert parsed_args.hf_overrides == {"key1": "val2"}
    assert parsed_args.optimization_level == 3
    assert parsed_args.compilation_config == {"mode": 2}

    assert len(caplog_vllm.records) == 1
    assert "duplicate" in caplog_vllm.text
    assert "--hf-overrides.key1" in caplog_vllm.text
    assert "--optimization-level" in caplog_vllm.text
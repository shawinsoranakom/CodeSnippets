def test_human_readable_model_len():
    # `exit_on_error` disabled to test invalid values below
    parser = EngineArgs.add_cli_args(FlexibleArgumentParser(exit_on_error=False))

    args = parser.parse_args([])
    assert args.max_model_len is None

    args = parser.parse_args(["--max-model-len", "1024"])
    assert args.max_model_len == 1024

    # Lower
    args = parser.parse_args(["--max-model-len", "1m"])
    assert args.max_model_len == 1_000_000
    args = parser.parse_args(["--max-model-len", "10k"])
    assert args.max_model_len == 10_000
    args = parser.parse_args(["--max-model-len", "2g"])
    assert args.max_model_len == 2_000_000_000
    args = parser.parse_args(["--max-model-len", "2t"])
    assert args.max_model_len == 2_000_000_000_000

    # Capital
    args = parser.parse_args(["--max-model-len", "3K"])
    assert args.max_model_len == 2**10 * 3
    args = parser.parse_args(["--max-model-len", "10M"])
    assert args.max_model_len == 2**20 * 10
    args = parser.parse_args(["--max-model-len", "4G"])
    assert args.max_model_len == 2**30 * 4
    args = parser.parse_args(["--max-model-len", "4T"])
    assert args.max_model_len == 2**40 * 4

    # Decimal values
    args = parser.parse_args(["--max-model-len", "10.2k"])
    assert args.max_model_len == 10200
    # ..truncated to the nearest int
    args = parser.parse_args(["--max-model-len", "10.2123451234567k"])
    assert args.max_model_len == 10212
    args = parser.parse_args(["--max-model-len", "10.2123451234567m"])
    assert args.max_model_len == 10212345
    args = parser.parse_args(["--max-model-len", "10.2123451234567g"])
    assert args.max_model_len == 10212345123
    args = parser.parse_args(["--max-model-len", "10.2123451234567t"])
    assert args.max_model_len == 10212345123456

    # Special value -1 for auto-fit to GPU memory
    args = parser.parse_args(["--max-model-len", "-1"])
    assert args.max_model_len == -1

    # 'auto' is an alias for -1
    args = parser.parse_args(["--max-model-len", "auto"])
    assert args.max_model_len == -1
    args = parser.parse_args(["--max-model-len", "AUTO"])
    assert args.max_model_len == -1

    # Invalid (do not allow decimals with binary multipliers)
    for invalid in ["1a", "pwd", "10.24", "1.23M", "1.22T"]:
        with pytest.raises(ArgumentError):
            parser.parse_args(["--max-model-len", invalid])
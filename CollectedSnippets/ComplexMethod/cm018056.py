def test_skip_pip_mutually_exclusive(mock_exit) -> None:
    """Test --skip-pip and --skip-pip-package are mutually exclusive."""

    def parse_args(*args):
        with patch("sys.argv", ["python", *args]):
            return main.get_arguments()

    args = parse_args("--skip-pip")
    assert args.skip_pip is True

    args = parse_args("--skip-pip-packages", "foo")
    assert args.skip_pip is False
    assert args.skip_pip_packages == ["foo"]

    args = parse_args("--skip-pip-packages", "foo-asd,bar-xyz")
    assert args.skip_pip is False
    assert args.skip_pip_packages == ["foo-asd", "bar-xyz"]

    assert mock_exit.called is False
    args = parse_args("--skip-pip", "--skip-pip-packages", "foo")
    assert mock_exit.called is True
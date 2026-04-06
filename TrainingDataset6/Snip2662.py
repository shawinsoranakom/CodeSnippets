def test_fastapi_cli_not_installed():
    with patch.object(fastapi.cli, "cli_main", None):
        with pytest.raises(RuntimeError) as exc_info:
            fastapi.cli.main()
        assert "To use the fastapi command, please install" in str(exc_info.value)
def get_runner():
    runner = CliRunner()
    with runner.isolated_filesystem():
        yield runner
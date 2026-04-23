def test_run_with_additional_arguments_env_files(
        self, docker_client: ContainerClient, tmp_path, monkeypatch
    ):
        env_variable = "TEST1=VAL1"
        env_file = tmp_path / "env1"
        env_vars = textwrap.dedent("""
            # Some comment
            TEST1=OVERRIDDEN
            TEST2=VAL2
            TEST3=${TEST2}
            TEST4=VAL # end comment
            TEST5="VAL"
            """)
        env_file.write_text(env_vars)

        stdout, _ = docker_client.run_container(
            "alpine",
            remove=True,
            command=["env"],
            additional_flags=f"-e {env_variable} --env-file {env_file}",
        )
        env_output = stdout.decode(config.DEFAULT_ENCODING)
        # behavior differs here from more advanced env file parsers
        assert env_variable in env_output
        assert "TEST1=VAL1" in env_output
        assert "TEST2=VAL2" in env_output
        assert "TEST3=${TEST2}" in env_output
        assert "TEST4=VAL # end comment" in env_output
        assert 'TEST5="VAL"' in env_output

        env_vars = textwrap.dedent("""
            # Some comment
            TEST1
            """)
        env_file.write_text(env_vars)

        stdout, _ = docker_client.run_container(
            "alpine",
            remove=True,
            command=["env"],
            additional_flags=f"--env-file {env_file}",
        )
        env_output = stdout.decode(config.DEFAULT_ENCODING)
        assert "TEST1" not in env_output

        monkeypatch.setenv("TEST1", "VAL1")
        stdout, _ = docker_client.run_container(
            "alpine",
            remove=True,
            command=["env"],
            additional_flags=f"--env-file {env_file}",
        )
        env_output = stdout.decode(config.DEFAULT_ENCODING)
        assert "TEST1=VAL1" in env_output

        env_vars = textwrap.dedent("""
            # Some comment
            TEST1=
            """)
        env_file.write_text(env_vars)

        stdout, _ = docker_client.run_container(
            "alpine",
            remove=True,
            command=["env"],
            additional_flags=f"--env-file {env_file}",
        )
        env_output = stdout.decode(config.DEFAULT_ENCODING)
        assert "TEST1=" in env_output.splitlines()
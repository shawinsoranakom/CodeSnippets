def test_docker_policy_spawns_docker_run(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    recorded: dict[str, list[str]] = {}

    def fake_launch(
        command: Sequence[str],
        *,
        env: Mapping[str, str],
        cwd: Path,
        start_new_session: bool,
        **_kwargs: Any,
    ) -> subprocess.Popen[str]:
        recorded["command"] = list(command)
        assert cwd == tmp_path
        assert "PATH" in env  # host environment should retain system PATH
        assert not start_new_session
        return Mock()

    monkeypatch.setattr(
        "langchain.agents.middleware._execution._launch_subprocess",
        fake_launch,
    )
    policy = DockerExecutionPolicy(
        image="ubuntu:22.04",
        memory_bytes=4096,
        extra_run_args=("--ipc", "host"),
    )

    env = {"PATH": "/bin"}
    policy.spawn(workspace=tmp_path, env=env, command=("/bin/bash",))

    command = recorded["command"]
    assert command[0] == shutil.which("docker")
    assert command[1:4] == ["run", "-i", "--rm"]
    assert "--memory" in command
    assert "4096" in command
    assert "-v" in command
    assert any(str(tmp_path) in part for part in command)
    assert "-w" in command
    w_index = command.index("-w")
    assert command[w_index + 1] == str(tmp_path)
    assert "-e" in command
    assert "PATH=/bin" in command
    assert command[-2:] == ["ubuntu:22.04", "/bin/bash"]
def test_docker_policy_skips_mount_for_temp_workspace(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(shutil, "which", lambda _: "/usr/bin/docker")

    recorded: dict[str, list[str]] = {}

    def fake_launch(command: Sequence[str], *, cwd: Path, **_kwargs: Any) -> subprocess.Popen[str]:
        recorded["command"] = list(command)
        assert cwd == workspace
        return Mock()

    monkeypatch.setattr(_execution, "_launch_subprocess", fake_launch)

    workspace = tmp_path / f"{_execution.SHELL_TEMP_PREFIX}case"
    workspace.mkdir()
    policy = DockerExecutionPolicy(cpus="1.5")
    env = {"PATH": "/bin"}
    policy.spawn(workspace=workspace, env=env, command=("/bin/sh",))

    command = recorded["command"]
    assert "-v" not in command
    assert "-w" in command
    w_index = command.index("-w")
    assert command[w_index + 1] == "/"
    assert "--cpus" in command
    assert "--network" in command
    assert "none" in command
    assert command[-2:] == [policy.image, "/bin/sh"]
def test_success_runs_all_steps_and_uses_env_and_workdir(monkeypatch, patch_module):
    run_test_plan = patch_module.run_test_plan

    tests_map = {
        "basic": {
            "title": "Basic suite",
            "package_install": [],
            "working_directory": "tests",
            "env_vars": {"GLOBAL_FLAG": "1"},
            "steps": [
                "export A=x && pytest -q",
                "export B=y && pytest -q tests/unit",
            ],
        }
    }

    # One exit code per step (export + two pytest)
    patch_module.run_command.side_effect = [0, 0, 0]

    run_test_plan("basic", "cpu", tests_map)

    calls = patch_module.run_command.call_args_list
    cmds = [_get_cmd(c) for c in calls]
    checks = [_get_check(c) for c in calls]

    if len(cmds) != 2:
        raise AssertionError(f"Expected 2 commands, got {len(cmds)}: {cmds}")
    if "pytest" not in cmds[0] or "pytest" not in cmds[1]:
        raise AssertionError(f"Expected pytest in both commands, got {cmds}")
    if not all(chk is False for chk in checks):
        raise AssertionError(f"Expected all checks to be False, got checks={checks}")

    if patch_module.workdir_calls != ["tests"]:
        raise AssertionError(
            f"Expected workdir_calls=['tests'], got {patch_module.workdir_calls}"
        )
    if patch_module.temp_calls != [{"GLOBAL_FLAG": "1"}]:
        raise AssertionError(
            f"Expected temp_calls=[{{'GLOBAL_FLAG': '1'}}], got {patch_module.temp_calls}"
        )
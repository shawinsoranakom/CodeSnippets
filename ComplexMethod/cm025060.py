async def test_script_vars_parallel() -> None:
    """Test script run variables parallel support."""
    script_vars = ScriptRunVariables.create_top_level({"x": 1, "y": 1, "z": 1})

    script_vars_2a = script_vars.enter_scope(parallel=True)
    script_vars_3a = script_vars_2a.enter_scope()

    script_vars_2b = script_vars.enter_scope(parallel=True)
    script_vars_3b = script_vars_2b.enter_scope()

    script_vars_3a["x"] = "a"
    script_vars_3a.assign_parallel_protected("y", "a")

    script_vars_3b["x"] = "b"
    script_vars_3b.assign_parallel_protected("y", "b")

    assert script_vars_3a._full_scope == {"x": "b", "y": "a", "z": 1}
    assert script_vars_3a.non_parallel_scope == {"x": "a", "y": "a"}

    assert script_vars_3b._full_scope == {"x": "b", "y": "b", "z": 1}
    assert script_vars_3b.non_parallel_scope == {"x": "b", "y": "b"}

    assert script_vars_3a.exit_scope() is script_vars_2a
    assert script_vars_2a.exit_scope() is script_vars
    assert script_vars_3b.exit_scope() is script_vars_2b
    assert script_vars_2b.exit_scope() is script_vars

    assert script_vars._full_scope == {"x": "b", "y": 1, "z": 1}
    assert script_vars.local_scope == {"x": "b", "y": 1, "z": 1}
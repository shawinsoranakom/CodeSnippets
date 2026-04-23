async def test_script_vars_scopes() -> None:
    """Test script run variables scopes."""
    script_vars = ScriptRunVariables.create_top_level()
    script_vars["x"] = 1
    script_vars["y"] = 1
    assert script_vars["x"] == 1
    assert script_vars["y"] == 1

    script_vars_2 = script_vars.enter_scope()
    script_vars_2.define_local("x", 2)
    assert script_vars_2["x"] == 2
    assert script_vars_2["y"] == 1

    script_vars_3 = script_vars_2.enter_scope()
    script_vars_3["x"] = 3
    script_vars_3["y"] = 3
    assert script_vars_3["x"] == 3
    assert script_vars_3["y"] == 3

    script_vars_4 = script_vars_3.enter_scope()
    assert script_vars_4["x"] == 3
    assert script_vars_4["y"] == 3

    assert script_vars_4.exit_scope() is script_vars_3

    assert script_vars_3._full_scope == {"x": 3, "y": 3}
    assert script_vars_3.local_scope == {}

    assert script_vars_3.exit_scope() is script_vars_2

    assert script_vars_2._full_scope == {"x": 3, "y": 3}
    assert script_vars_2.local_scope == {"x": 3}

    assert script_vars_2.exit_scope() is script_vars

    assert script_vars._full_scope == {"x": 1, "y": 3}
    assert script_vars.local_scope == {"x": 1, "y": 3}
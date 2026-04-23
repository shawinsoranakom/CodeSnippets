def test_config_passthrough_nested() -> None:
    runnable = MyRunnable(my_property="a")
    configurable_runnable = runnable.configurable_fields(
        my_property=ConfigurableField(
            id="my_property",
            name="My property",
            description="The property to test",
        )
    ).configurable_alternatives(
        ConfigurableField(id="which", description="Which runnable to use"),
        other=MyOtherRunnable(my_other_property="c"),
    )
    # first one
    with pytest.raises(AttributeError):
        configurable_runnable.not_my_custom_function()  # type: ignore[attr-defined]
    assert configurable_runnable.my_custom_function() == "a"  # type: ignore[attr-defined]
    assert (
        configurable_runnable.my_custom_function_w_config(  # type: ignore[attr-defined]
            {"configurable": {"my_property": "b"}}
        )
        == "b"
    )
    assert (
        configurable_runnable.my_custom_function_w_config(  # type: ignore[attr-defined]
            config={"configurable": {"my_property": "b"}}
        )
        == "b"
    )
    assert (
        configurable_runnable.with_config(
            configurable={"my_property": "b"}
        ).my_custom_function()  # type: ignore[attr-defined]
        == "b"
    ), "function without config can be called w bound config"
    assert (
        configurable_runnable.with_config(
            configurable={"my_property": "b"}
        ).my_custom_function_w_config(  # type: ignore[attr-defined]
        )
        == "b"
    ), "func with config arg can be called w bound config without config"
    assert (
        configurable_runnable.with_config(
            configurable={"my_property": "b"}
        ).my_custom_function_w_config(  # type: ignore[attr-defined]
            config={"configurable": {"my_property": "c"}}
        )
        == "c"
    ), "func with config arg can be called w bound config with config as kwarg"
    assert (
        configurable_runnable.with_config(
            configurable={"my_property": "b"}
        ).my_custom_function_w_kw_config(  # type: ignore[attr-defined]
        )
        == "b"
    ), "function with config kwarg can be called w bound config w/out config"
    assert (
        configurable_runnable.with_config(
            configurable={"my_property": "b"}
        ).my_custom_function_w_kw_config(  # type: ignore[attr-defined]
            config={"configurable": {"my_property": "c"}}
        )
        == "c"
    ), "function with config kwarg can be called w bound config with config"
    assert (
        configurable_runnable.with_config(configurable={"my_property": "b"})
        .with_types()
        .my_custom_function()  # type: ignore[attr-defined]
        == "b"
    ), "function without config can be called w bound config"
    assert (
        configurable_runnable.with_config(configurable={"my_property": "b"})
        .with_types()
        .my_custom_function_w_config(  # type: ignore[attr-defined]
        )
        == "b"
    ), "func with config arg can be called w bound config without config"
    assert (
        configurable_runnable.with_config(configurable={"my_property": "b"})
        .with_types()
        .my_custom_function_w_config(  # type: ignore[attr-defined]
            config={"configurable": {"my_property": "c"}}
        )
        == "c"
    ), "func with config arg can be called w bound config with config as kwarg"
    assert (
        configurable_runnable.with_config(configurable={"my_property": "b"})
        .with_types()
        .my_custom_function_w_kw_config(  # type: ignore[attr-defined]
        )
        == "b"
    ), "function with config kwarg can be called w bound config w/out config"
    assert (
        configurable_runnable.with_config(configurable={"my_property": "b"})
        .with_types()
        .my_custom_function_w_kw_config(  # type: ignore[attr-defined]
            config={"configurable": {"my_property": "c"}}
        )
        == "c"
    ), "function with config kwarg can be called w bound config with config"
    # second one
    with pytest.raises(AttributeError):
        configurable_runnable.my_other_custom_function()  # type: ignore[attr-defined]
    with pytest.raises(AttributeError):
        configurable_runnable.my_other_custom_function_w_config(  # type: ignore[attr-defined]
            {"configurable": {"my_other_property": "b"}}
        )
    with pytest.raises(AttributeError):
        configurable_runnable.with_config(
            configurable={"my_other_property": "c", "which": "other"}
        ).my_other_custom_function()
async def test_function_tool() -> None:
    """Test FunctionTool with different function types and features."""

    # Test sync and async functions
    def sync_func(x: int, y: str) -> str:
        return y * x

    async def async_func(x: float, y: float, cancellation_token: CancellationToken) -> float:
        if cancellation_token.is_cancelled():
            raise Exception("Cancelled")
        return x + y

    # Create tools with different configurations
    sync_tool = FunctionTool(
        func=sync_func, description="Multiply string", global_imports=[ImportFromModule("typing", ("Dict",))]
    )
    invalid_import_sync_tool = FunctionTool(
        func=sync_func, description="Multiply string", global_imports=[ImportFromModule("invalid_module (", ("Dict",))]
    )

    invalid_import_config = invalid_import_sync_tool.dump_component()
    # check that invalid import raises an error
    with pytest.raises(RuntimeError):
        _ = FunctionTool.load_component(invalid_import_config, FunctionTool)

    async_tool = FunctionTool(
        func=async_func,
        description="Add numbers",
        name="custom_adder",
        global_imports=[ImportFromModule("autogen_core", ("CancellationToken",))],
    )

    # Test serialization and config

    sync_config = sync_tool.dump_component()
    assert isinstance(sync_config, ComponentModel)
    assert sync_config.config["name"] == "sync_func"
    assert len(sync_config.config["global_imports"]) == 1
    assert not sync_config.config["has_cancellation_support"]

    async_config = async_tool.dump_component()
    assert async_config.config["name"] == "custom_adder"
    assert async_config.config["has_cancellation_support"]

    # Test deserialization and execution
    loaded_sync = FunctionTool.load_component(sync_config, FunctionTool)
    loaded_async = FunctionTool.load_component(async_config, FunctionTool)

    # Test execution and validation
    token = CancellationToken()
    assert await loaded_sync.run_json({"x": 2, "y": "test"}, token) == "testtest"
    assert await loaded_async.run_json({"x": 1.5, "y": 2.5}, token) == 4.0

    # Test error cases
    with pytest.raises(ValueError):
        # Type error
        await loaded_sync.run_json({"x": "invalid", "y": "test"}, token)

    cancelled_token = CancellationToken()
    cancelled_token.cancel()
    with pytest.raises(Exception, match="Cancelled"):
        await loaded_async.run_json({"x": 1.0, "y": 2.0}, cancelled_token)
async def test_mcp_workbench_server_filesystem() -> None:
    params = StdioServerParams(
        command="npx",
        args=[
            "-y",
            "@modelcontextprotocol/server-filesystem",
            ".",
        ],
        read_timeout_seconds=60,
    )

    workbench = McpWorkbench(server_params=params)
    await workbench.start()

    tools = await workbench.list_tools()
    assert tools is not None
    tools = [tool for tool in tools if tool["name"] == "read_file"]
    assert len(tools) == 1
    tool = tools[0]
    result = await workbench.call_tool(tool["name"], {"path": "README.md"}, CancellationToken())
    assert result is not None

    await workbench.stop()

    # Serialize the workbench.
    config = workbench.dump_component()

    # Deserialize the workbench.
    async with Workbench.load_component(config) as new_workbench:
        tools = await new_workbench.list_tools()
        assert tools is not None
        tools = [tool for tool in tools if tool["name"] == "read_file"]
        assert len(tools) == 1
        tool = tools[0]
        result = await new_workbench.call_tool(tool["name"], {"path": "README.md"}, CancellationToken())
        assert result is not None
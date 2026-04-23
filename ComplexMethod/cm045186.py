async def test_mcp_server_git_existing_session() -> None:
    params = StdioServerParams(
        command="uvx",
        args=["mcp-server-git"],
        read_timeout_seconds=60,
    )
    async with create_mcp_server_session(params) as session:
        await session.initialize()
        tools = await mcp_server_tools(server_params=params, session=session)
        assert tools is not None
        git_log = [tool for tool in tools if tool.name == "git_log"][0]
        repo_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")
        result = await git_log.run_json({"repo_path": repo_path}, CancellationToken())
        assert result is not None

        git_status = [tool for tool in tools if tool.name == "git_status"][0]
        result = await git_status.run_json({"repo_path": repo_path}, CancellationToken())
        assert result is not None
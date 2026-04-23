async def test_fetch_mcp_via_stdio(
    temp_dir, runtime_cls, run_as_openhands, dynamic_port
):
    mcp_stdio_server_config = StdioMCPServer(
        name='fetch', command='uvx', args=['mcp-server-fetch']
    )
    override_mcp_config = MCPConfig(stdio_servers=[mcp_stdio_server_config])
    runtime, config = _load_runtime(
        temp_dir,
        runtime_cls,
        run_as_openhands,
        override_mcp_config=override_mcp_config,
        enable_browser=True,
    )

    # Test browser server
    action_cmd = CmdRunAction(
        command=f'python3 -m http.server {dynamic_port} > server.log 2>&1 &'
    )
    logger.info(action_cmd, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action_cmd)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})

    assert isinstance(obs, CmdOutputObservation)
    assert obs.exit_code == 0
    assert '[1]' in obs.content

    action_cmd = CmdRunAction(command='sleep 3 && cat server.log')
    logger.info(action_cmd, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action_cmd)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.exit_code == 0

    mcp_action = MCPAction(
        name='fetch', arguments={'url': f'http://localhost:{dynamic_port}'}
    )
    obs = await runtime.call_tool_mcp(mcp_action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert isinstance(obs, MCPObservation), (
        'The observation should be a MCPObservation.'
    )

    result_json = json.loads(obs.content)
    assert not result_json['isError']
    assert len(result_json['content']) == 1
    assert result_json['content'][0]['type'] == 'text'
    assert (
        result_json['content'][0]['text']
        == f'Contents of http://localhost:{dynamic_port}/:\n---\n\n* <.downloads/>\n* <server.log>\n\n---'
    )

    runtime.close()
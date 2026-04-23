async def test_both_stdio_and_sse_mcp(
    temp_dir, runtime_cls, run_as_openhands, sse_mcp_docker_server, dynamic_port
):
    sse_server_info = sse_mcp_docker_server
    sse_url = sse_server_info['url']
    runtime = None
    try:
        override_mcp_config = MCPConfig(
            mcpServers={
                'fs': RemoteMCPServer(url=sse_url, transport='sse'),
                'fetch': StdioMCPServer(command='uvx', args=['mcp-server-fetch']),
            }
        )
        runtime, config = _load_runtime(
            temp_dir,
            runtime_cls,
            run_as_openhands,
            override_mcp_config=override_mcp_config,
            enable_browser=True,
        )

        # ======= Test SSE server =======
        mcp_action_sse = MCPAction(name='list_directory', arguments={'path': '.'})
        obs_sse = await runtime.call_tool_mcp(mcp_action_sse)
        logger.info(obs_sse, extra={'msg_type': 'OBSERVATION'})
        assert isinstance(obs_sse, MCPObservation), (
            'The observation should be a MCPObservation.'
        )
        assert '[FILE] .dockerenv' in obs_sse.content

        # ======= Test stdio server =======
        # Test browser server
        action_cmd_http = CmdRunAction(
            command=f'python3 -m http.server {dynamic_port} > server.log 2>&1 &'
        )
        logger.info(action_cmd_http, extra={'msg_type': 'ACTION'})
        obs_http = runtime.run_action(action_cmd_http)
        logger.info(obs_http, extra={'msg_type': 'OBSERVATION'})

        assert isinstance(obs_http, CmdOutputObservation)
        assert obs_http.exit_code == 0
        assert '[1]' in obs_http.content

        action_cmd_cat = CmdRunAction(command='sleep 3 && cat server.log')
        logger.info(action_cmd_cat, extra={'msg_type': 'ACTION'})
        obs_cat = runtime.run_action(action_cmd_cat)
        logger.info(obs_cat, extra={'msg_type': 'OBSERVATION'})
        assert obs_cat.exit_code == 0

        mcp_action_fetch = MCPAction(
            # NOTE: the tool name is `fetch_fetch` because the tool name is `fetch`
            # And FastMCP Proxy will pre-pend the server name (in this case, `fetch`)
            # to the tool name, so the full tool name becomes `fetch_fetch`
            name='fetch',
            arguments={'url': f'http://localhost:{dynamic_port}'},
        )
        obs_fetch = await runtime.call_tool_mcp(mcp_action_fetch)
        logger.info(obs_fetch, extra={'msg_type': 'OBSERVATION'})
        assert isinstance(obs_fetch, MCPObservation), (
            'The observation should be a MCPObservation.'
        )

        result_json = json.loads(obs_fetch.content)
        assert not result_json['isError']
        assert len(result_json['content']) == 1
        assert result_json['content'][0]['type'] == 'text'
        assert (
            result_json['content'][0]['text']
            == f'Contents of http://localhost:{dynamic_port}/:\n---\n\n* <.downloads/>\n* <server.log>\n\n---'
        )
    finally:
        if runtime:
            runtime.close()
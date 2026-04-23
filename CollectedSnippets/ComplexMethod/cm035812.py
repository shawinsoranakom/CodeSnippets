async def test_microagent_and_one_stdio_mcp_in_config(
    temp_dir, runtime_cls, run_as_openhands, dynamic_port
):
    runtime = None
    try:
        filesystem_config = StdioMCPServer(
            name='filesystem',
            command='npx',
            args=[
                '@modelcontextprotocol/server-filesystem@2025.8.18',
                '/',
            ],
        )
        override_mcp_config = MCPConfig(stdio_servers=[filesystem_config])
        runtime, config = _load_runtime(
            temp_dir,
            runtime_cls,
            run_as_openhands,
            override_mcp_config=override_mcp_config,
            enable_browser=True,
        )

        # NOTE: this simulate the case where the microagent adds a new stdio server to the runtime
        # but that stdio server is not in the initial config
        # Actual invocation of the microagent involves `add_mcp_tools_to_agent`
        # which will call `get_mcp_config` with the stdio server from microagent's config
        fetch_config = StdioMCPServer(
            name='fetch', command='uvx', args=['mcp-server-fetch']
        )
        updated_config = runtime.get_mcp_config([fetch_config])
        logger.info(f'updated_config: {updated_config}')

        # ======= Test the stdio server in the config =======
        mcp_action_sse = MCPAction(
            name='filesystem_list_directory', arguments={'path': '/'}
        )
        obs_sse = await runtime.call_tool_mcp(mcp_action_sse)
        logger.info(obs_sse, extra={'msg_type': 'OBSERVATION'})
        assert isinstance(obs_sse, MCPObservation), (
            'The observation should be a MCPObservation.'
        )
        assert '[FILE] .dockerenv' in obs_sse.content

        # ======= Test the stdio server added by the microagent =======
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
            name='fetch_fetch', arguments={'url': f'http://localhost:{dynamic_port}'}
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
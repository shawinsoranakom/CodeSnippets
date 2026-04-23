def test_simple_browse(temp_dir, runtime_cls, run_as_openhands, dynamic_port):
    runtime, config = _load_runtime(
        temp_dir, runtime_cls, run_as_openhands, enable_browser=True
    )

    # Test browse
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

    action_browse = BrowseURLAction(
        url=f'http://localhost:{dynamic_port}', return_axtree=False
    )
    logger.info(action_browse, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action_browse)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})

    assert isinstance(obs, BrowserOutputObservation)
    assert f'http://localhost:{dynamic_port}' in obs.url
    assert not obs.error
    assert obs.open_pages_urls == [f'http://localhost:{dynamic_port}/']
    assert obs.active_page_index == 0
    assert obs.last_browser_action == f'goto("http://localhost:{dynamic_port}")'
    assert obs.last_browser_action_error == ''
    assert 'Directory listing for /' in obs.content
    assert 'server.log' in obs.content

    # clean up
    action = CmdRunAction(command='rm -rf server.log')
    logger.info(action, extra={'msg_type': 'ACTION'})
    obs = runtime.run_action(action)
    logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    assert obs.exit_code == 0

    _close_test_runtime(runtime)
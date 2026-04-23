def test_browser_navigation_actions(
    temp_dir, runtime_cls, run_as_openhands, dynamic_port
):
    """Test browser navigation actions: goto, go_back, go_forward, noop."""
    runtime, config = _load_runtime(
        temp_dir, runtime_cls, run_as_openhands, enable_browser=True
    )
    try:
        # Create test HTML pages
        page1_content = """
        <!DOCTYPE html>
        <html>
        <head><title>Page 1</title></head>
        <body>
            <h1>Page 1</h1>
            <a href="page2.html" id="link-to-page2">Go to Page 2</a>
        </body>
        </html>
        """

        page2_content = """
        <!DOCTYPE html>
        <html>
        <head><title>Page 2</title></head>
        <body>
            <h1>Page 2</h1>
            <a href="page1.html" id="link-to-page1">Go to Page 1</a>
        </body>
        </html>
        """

        # Create HTML files in temp directory
        page1_path = os.path.join(temp_dir, 'page1.html')
        page2_path = os.path.join(temp_dir, 'page2.html')

        with open(page1_path, 'w') as f:
            f.write(page1_content)
        with open(page2_path, 'w') as f:
            f.write(page2_content)

        # Copy files to sandbox
        sandbox_dir = config.workspace_mount_path_in_sandbox
        runtime.copy_to(page1_path, sandbox_dir)
        runtime.copy_to(page2_path, sandbox_dir)

        # Start HTTP server
        action_cmd = CmdRunAction(
            command=f'python3 -m http.server {dynamic_port} > server.log 2>&1 &'
        )
        logger.info(action_cmd, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_cmd)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert obs.exit_code == 0

        # Wait for server to start
        action_cmd = CmdRunAction(command='sleep 3')
        logger.info(action_cmd, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_cmd)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        # Test goto action
        action_browse = BrowseInteractiveAction(
            browser_actions=f'goto("http://localhost:{dynamic_port}/page1.html")',
            return_axtree=False,
        )
        logger.info(action_browse, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_browse)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        assert isinstance(obs, BrowserOutputObservation)
        assert not obs.error
        assert 'Page 1' in obs.content
        assert f'http://localhost:{dynamic_port}/page1.html' in obs.url

        # Test noop action (should not change page)
        action_browse = BrowseInteractiveAction(
            browser_actions='noop(500)', return_axtree=False
        )
        logger.info(action_browse, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_browse)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        assert isinstance(obs, BrowserOutputObservation)
        assert not obs.error
        assert 'Page 1' in obs.content
        assert f'http://localhost:{dynamic_port}/page1.html' in obs.url

        # Navigate to page 2
        action_browse = BrowseInteractiveAction(
            browser_actions=f'goto("http://localhost:{dynamic_port}/page2.html")',
            return_axtree=False,
        )
        logger.info(action_browse, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_browse)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        assert isinstance(obs, BrowserOutputObservation)
        assert not obs.error
        assert 'Page 2' in obs.content
        assert f'http://localhost:{dynamic_port}/page2.html' in obs.url

        # Test go_back action
        action_browse = BrowseInteractiveAction(
            browser_actions='go_back()', return_axtree=False
        )
        logger.info(action_browse, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_browse)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        assert isinstance(obs, BrowserOutputObservation)
        assert not obs.error
        assert 'Page 1' in obs.content
        assert f'http://localhost:{dynamic_port}/page1.html' in obs.url

        # Test go_forward action
        action_browse = BrowseInteractiveAction(
            browser_actions='go_forward()', return_axtree=False
        )
        logger.info(action_browse, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_browse)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        assert isinstance(obs, BrowserOutputObservation)
        assert not obs.error
        assert 'Page 2' in obs.content
        assert f'http://localhost:{dynamic_port}/page2.html' in obs.url

        # Clean up
        action_cmd = CmdRunAction(command='pkill -f "python3 -m http.server" || true')
        logger.info(action_cmd, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_cmd)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

    finally:
        _close_test_runtime(runtime)
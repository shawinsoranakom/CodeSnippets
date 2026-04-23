def test_browser_interactive_actions(
    temp_dir, runtime_cls, run_as_openhands, dynamic_port
):
    """Test browser interactive actions: scroll, hover, fill, press, focus."""
    runtime, config = _load_runtime(
        temp_dir, runtime_cls, run_as_openhands, enable_browser=True
    )
    try:
        # Create a test page with scrollable content
        scroll_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Scroll Test</title>
            <style>
                body { margin: 0; padding: 20px; }
                .content { height: 2000px; background: linear-gradient(to bottom, #ff0000, #0000ff); }
                .hover-target {
                    width: 200px; height: 100px; background: #ccc; margin: 20px;
                    border: 2px solid #000; cursor: pointer;
                }
                .hover-target:hover { background: #ffff00; }
                #focus-input { margin: 20px; padding: 10px; font-size: 16px; }
            </style>
        </head>
        <body>
            <h1>Interactive Test Page</h1>
            <div class="hover-target" id="hover-div">Hover over me</div>
            <input type="text" id="focus-input" placeholder="Focus me and type">
            <div class="content">
                <p>This is a long scrollable page...</p>
                <p style="margin-top: 500px;">Middle content</p>
                <p style="margin-top: 500px;" id="bottom-content">Bottom content</p>
            </div>
        </body>
        </html>
        """

        # Create HTML file
        scroll_path = os.path.join(temp_dir, 'scroll.html')
        with open(scroll_path, 'w') as f:
            f.write(scroll_content)

        # Copy to sandbox
        sandbox_dir = config.workspace_mount_path_in_sandbox
        runtime.copy_to(scroll_path, sandbox_dir)

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

        # Navigate to scroll page
        action_browse = BrowseInteractiveAction(
            browser_actions=f'goto("http://localhost:{dynamic_port}/scroll.html")',
            return_axtree=True,
        )
        logger.info(action_browse, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_browse)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        assert isinstance(obs, BrowserOutputObservation)
        assert not obs.error
        assert 'Interactive Test Page' in obs.content

        # Test scroll action
        action_browse = BrowseInteractiveAction(
            browser_actions='scroll(0, 300)',  # Scroll down 300 pixels
            return_axtree=True,
        )
        logger.info(action_browse, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_browse)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        assert isinstance(obs, BrowserOutputObservation)
        assert not obs.error, f'Scroll action failed: {obs.last_browser_action_error}'
        # Verify the scroll action was recorded correctly
        assert 'scroll(0, 300)' in obs.last_browser_action, (
            f'Expected scroll action in browser history but got: {obs.last_browser_action}'
        )

        # Parse the axtree to get actual bid values for interactive elements
        axtree_elements = parse_axtree_content(obs.content)

        # Find elements by their characteristics visible in the axtree
        hover_div_bid = find_element_by_text(axtree_elements, 'Hover over me')
        focus_input_bid = find_element_by_text(axtree_elements, 'Focus me and type')

        # Verify we found the required elements
        assert hover_div_bid is not None, (
            f'Could not find hover div element in axtree. Available elements: {dict(list(axtree_elements.items())[:5])}'
        )
        assert focus_input_bid is not None, (
            f'Could not find focus input element in axtree. Available elements: {dict(list(axtree_elements.items())[:5])}'
        )

        # Test hover action with real bid
        action_browse = BrowseInteractiveAction(
            browser_actions=f'hover("{hover_div_bid}")', return_axtree=True
        )
        logger.info(action_browse, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_browse)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        assert isinstance(obs, BrowserOutputObservation)
        assert not obs.error, f'Hover action failed: {obs.last_browser_action_error}'

        # Test focus action with real bid
        action_browse = BrowseInteractiveAction(
            browser_actions=f'focus("{focus_input_bid}")', return_axtree=True
        )
        logger.info(action_browse, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_browse)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        assert isinstance(obs, BrowserOutputObservation)
        assert not obs.error, f'Focus action failed: {obs.last_browser_action_error}'

        # Verify that the input element is now focused
        assert obs.focused_element_bid == focus_input_bid, (
            f'Expected focused element to be {focus_input_bid}, but got {obs.focused_element_bid}'
        )

        # Test fill action (type in focused input) with real bid
        action_browse = BrowseInteractiveAction(
            browser_actions=f'fill("{focus_input_bid}", "TestValue123")',
            return_axtree=True,
        )
        logger.info(action_browse, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_browse)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        assert isinstance(obs, BrowserOutputObservation)
        assert not obs.error, f'Fill action failed: {obs.last_browser_action_error}'

        # Verify that the text was actually entered
        updated_axtree_elements = parse_axtree_content(obs.content)
        assert focus_input_bid in updated_axtree_elements, (
            f'Focus input element {focus_input_bid} should be present in updated axtree. Available elements: {list(updated_axtree_elements.keys())[:10]}'
        )
        input_desc = updated_axtree_elements[focus_input_bid]
        assert 'TestValue123' in input_desc or "'TestValue123'" in input_desc, (
            f"Input should contain 'TestValue123' but description is: {input_desc}"
        )

        # Test press action (for pressing individual keys) with real bid
        action_browse = BrowseInteractiveAction(
            browser_actions=f'press("{focus_input_bid}", "Backspace")',
            return_axtree=True,
        )
        logger.info(action_browse, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_browse)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        assert isinstance(obs, BrowserOutputObservation)
        assert not obs.error, f'Press action failed: {obs.last_browser_action_error}'

        # Verify the backspace removed the last character (3 from TestValue123)
        updated_axtree_elements = parse_axtree_content(obs.content)
        assert focus_input_bid in updated_axtree_elements, (
            f'Focus input element {focus_input_bid} should be present in updated axtree. Available elements: {list(updated_axtree_elements.keys())[:10]}'
        )
        input_desc = updated_axtree_elements[focus_input_bid]
        assert 'TestValue12' in input_desc or "'TestValue12'" in input_desc, (
            f"Input should contain 'TestValue12' after backspace but description is: {input_desc}"
        )

        # Test multiple actions in sequence
        action_browse = BrowseInteractiveAction(
            browser_actions="""
scroll(0, -200)
noop(1000)
scroll(0, 400)
""".strip(),
            return_axtree=False,
        )
        logger.info(action_browse, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_browse)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        assert isinstance(obs, BrowserOutputObservation)
        assert not obs.error, (
            f'Multiple actions sequence failed: {obs.last_browser_action_error}'
        )
        # Verify the last action in the sequence was recorded
        assert (
            'scroll(0, 400)' in obs.last_browser_action
            or 'noop(1000)' in obs.last_browser_action
        ), f'Expected final action from sequence but got: {obs.last_browser_action}'

        # Clean up
        action_cmd = CmdRunAction(command='pkill -f "python3 -m http.server" || true')
        logger.info(action_cmd, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_cmd)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

    finally:
        _close_test_runtime(runtime)
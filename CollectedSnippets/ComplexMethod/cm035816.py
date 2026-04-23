def test_browser_form_interactions(
    temp_dir, runtime_cls, run_as_openhands, dynamic_port
):
    """Test browser form interaction actions: fill, click, select_option, clear."""
    runtime, config = _load_runtime(
        temp_dir, runtime_cls, run_as_openhands, enable_browser=True
    )
    try:
        # Create a test form page
        form_content = """
        <!DOCTYPE html>
        <html>
        <head><title>Test Form</title></head>
        <body>
            <h1>Test Form</h1>
            <form id="test-form">
                <input type="text" id="text-input" name="text" placeholder="Enter text">
                <textarea id="textarea-input" name="message" placeholder="Enter message"></textarea>
                <select id="select-input" name="option">
                    <option value="">Select an option</option>
                    <option value="option1">Option 1</option>
                    <option value="option2">Option 2</option>
                    <option value="option3">Option 3</option>
                </select>
                <button type="button" id="test-button">Test Button</button>
                <input type="submit" id="submit-button" value="Submit">
            </form>
            <div id="result"></div>
            <script>
                document.getElementById('test-button').onclick = function() {
                    document.getElementById('result').innerHTML = 'Button clicked!';
                };
            </script>
        </body>
        </html>
        """

        # Create HTML file
        form_path = os.path.join(temp_dir, 'form.html')
        with open(form_path, 'w') as f:
            f.write(form_content)

        # Copy to sandbox
        sandbox_dir = config.workspace_mount_path_in_sandbox
        runtime.copy_to(form_path, sandbox_dir)

        # Start HTTP server
        action_cmd = CmdRunAction(
            command=f'python3 -m http.server {dynamic_port} > server.log 2>&1 &'
        )
        logger.info(action_cmd, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_cmd)
        logger.info(obs, extra={'msg_type': 'ACTION'})
        assert obs.exit_code == 0

        # Wait for server to start
        action_cmd = CmdRunAction(command='sleep 3')
        logger.info(action_cmd, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_cmd)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        # Navigate to form page
        action_browse = BrowseInteractiveAction(
            browser_actions=f'goto("http://localhost:{dynamic_port}/form.html")',
            return_axtree=True,  # Need axtree to get element bids
        )
        logger.info(action_browse, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_browse)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        assert isinstance(obs, BrowserOutputObservation)
        assert not obs.error
        assert 'Test Form' in obs.content

        # Parse the axtree to get actual bid values
        axtree_elements = parse_axtree_content(obs.content)

        # Find elements by their characteristics visible in the axtree
        text_input_bid = find_element_by_text(axtree_elements, 'Enter text')
        textarea_bid = find_element_by_text(axtree_elements, 'Enter message')
        select_bid = find_element_by_text(axtree_elements, 'combobox')
        button_bid = find_element_by_text(axtree_elements, 'Test Button')

        # Verify we found the correct elements
        assert text_input_bid is not None, (
            f'Could not find text input element in axtree. Available elements: {dict(list(axtree_elements.items())[:5])}'
        )
        assert textarea_bid is not None, (
            f'Could not find textarea element in axtree. Available elements: {dict(list(axtree_elements.items())[:5])}'
        )
        assert button_bid is not None, (
            f'Could not find button element in axtree. Available elements: {dict(list(axtree_elements.items())[:5])}'
        )
        assert select_bid is not None, (
            f'Could not find select element in axtree. Available elements: {dict(list(axtree_elements.items())[:5])}'
        )
        assert text_input_bid != button_bid, (
            'Text input bid should be different from button bid'
        )

        # Test fill action with real bid values
        action_browse = BrowseInteractiveAction(
            browser_actions=f"""
fill("{text_input_bid}", "Hello World")
fill("{textarea_bid}", "This is a test message")
""".strip(),
            return_axtree=True,
        )
        logger.info(action_browse, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_browse)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        assert isinstance(obs, BrowserOutputObservation)
        # Verify the action executed successfully
        assert not obs.error, (
            f'Browser action failed with error: {obs.last_browser_action_error}'
        )

        # Parse the updated axtree to verify the text was actually filled
        updated_axtree_elements = parse_axtree_content(obs.content)

        # Check that the text input now contains our text
        assert text_input_bid in updated_axtree_elements, (
            f'Text input element {text_input_bid} should be present in updated axtree. Available elements: {list(updated_axtree_elements.keys())[:10]}'
        )
        text_input_desc = updated_axtree_elements[text_input_bid]
        # The filled value should appear in the element description (axtree shows values differently)
        assert 'Hello World' in text_input_desc or "'Hello World'" in text_input_desc, (
            f"Text input should contain 'Hello World' but description is: {text_input_desc}"
        )

        assert textarea_bid in updated_axtree_elements, (
            f'Textarea element {textarea_bid} should be present in updated axtree. Available elements: {list(updated_axtree_elements.keys())[:10]}'
        )
        textarea_desc = updated_axtree_elements[textarea_bid]
        assert (
            'This is a test message' in textarea_desc
            or "'This is a test message'" in textarea_desc
        ), f'Textarea should contain test message but description is: {textarea_desc}'

        # Test select_option action with real bid
        action_browse = BrowseInteractiveAction(
            browser_actions=f'select_option("{select_bid}", "option2")',
            return_axtree=True,
        )
        logger.info(action_browse, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_browse)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        assert isinstance(obs, BrowserOutputObservation)
        assert not obs.error, (
            f'Select option action failed: {obs.last_browser_action_error}'
        )

        # Verify that option2 is now selected
        updated_axtree_elements = parse_axtree_content(obs.content)
        assert select_bid in updated_axtree_elements, (
            f'Select element {select_bid} should be present in updated axtree. Available elements: {list(updated_axtree_elements.keys())[:10]}'
        )
        select_desc = updated_axtree_elements[select_bid]
        # The selected option should be reflected in the select element description
        assert 'option2' in select_desc or 'Option 2' in select_desc, (
            f"Select element should show 'option2' as selected but description is: {select_desc}"
        )

        # Test click action with real bid
        action_browse = BrowseInteractiveAction(
            browser_actions=f'click("{button_bid}")', return_axtree=True
        )
        obs = runtime.run_action(action_browse)
        assert isinstance(obs, BrowserOutputObservation)
        assert not obs.error, f'Click action failed: {obs.last_browser_action_error}'

        # Verify that the button click triggered the JavaScript and updated the result div
        updated_axtree_elements = parse_axtree_content(obs.content)
        # Look for the "Button clicked!" text that should appear in the result div
        result_found = any(
            'Button clicked!' in desc for desc in updated_axtree_elements.values()
        )
        assert result_found, (
            f"Button click should have triggered JavaScript to show 'Button clicked!' but not found in: {dict(list(updated_axtree_elements.items())[:10])}"
        )

        # Test clear action with real bid
        action_browse = BrowseInteractiveAction(
            browser_actions=f'clear("{text_input_bid}")', return_axtree=True
        )
        obs = runtime.run_action(action_browse)
        assert isinstance(obs, BrowserOutputObservation)
        assert not obs.error, f'Clear action failed: {obs.last_browser_action_error}'

        # Verify that the text input is now empty/cleared
        updated_axtree_elements = parse_axtree_content(obs.content)
        assert text_input_bid in updated_axtree_elements
        text_input_desc = updated_axtree_elements[text_input_bid]
        # After clearing, the input should not contain the previous text
        assert 'Hello World' not in text_input_desc, (
            f'Text input should be cleared but still contains text: {text_input_desc}'
        )
        # Check that it's back to showing placeholder text or is empty
        assert (
            'Enter text' in text_input_desc  # placeholder text
            or 'textbox' in text_input_desc.lower()  # generic textbox description
            or text_input_desc.strip() == ''  # empty description
        ), (
            f'Cleared text input should show placeholder or be empty but description is: {text_input_desc}'
        )

        # Clean up
        action_cmd = CmdRunAction(command='pkill -f "python3 -m http.server" || true')
        logger.info(action_cmd, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_cmd)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

    finally:
        _close_test_runtime(runtime)
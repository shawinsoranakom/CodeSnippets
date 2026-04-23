def test_browser_file_upload(temp_dir, runtime_cls, run_as_openhands, dynamic_port):
    """Test browser file upload action."""
    runtime, config = _load_runtime(
        temp_dir, runtime_cls, run_as_openhands, enable_browser=True
    )
    try:
        # Create a test file to upload
        test_file_content = 'This is a test file for upload testing.'
        test_file_path = os.path.join(temp_dir, 'upload_test.txt')
        with open(test_file_path, 'w') as f:
            f.write(test_file_content)

        # Create an upload form page
        upload_content = """
        <!DOCTYPE html>
        <html>
        <head><title>File Upload Test</title></head>
        <body>
            <h1>File Upload Test</h1>
            <form enctype="multipart/form-data">
                <input type="file" id="file-input" name="file" accept=".txt,.pdf,.png">
                <button type="button" onclick="handleUpload()">Upload File</button>
            </form>
            <div id="upload-result"></div>
            <script>
                function handleUpload() {
                    const fileInput = document.getElementById('file-input');
                    if (fileInput.files.length > 0) {
                        document.getElementById('upload-result').innerHTML =
                            'File selected: ' + fileInput.files[0].name;
                    } else {
                        document.getElementById('upload-result').innerHTML = 'No file selected';
                    }
                }
            </script>
        </body>
        </html>
        """

        # Create HTML file
        upload_path = os.path.join(temp_dir, 'upload.html')
        with open(upload_path, 'w') as f:
            f.write(upload_content)

        # Copy files to sandbox
        sandbox_dir = config.workspace_mount_path_in_sandbox
        runtime.copy_to(upload_path, sandbox_dir)
        runtime.copy_to(test_file_path, sandbox_dir)

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

        # Navigate to upload page
        action_browse = BrowseInteractiveAction(
            browser_actions=f'goto("http://localhost:{dynamic_port}/upload.html")',
            return_axtree=True,
        )
        logger.info(action_browse, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_browse)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        assert isinstance(obs, BrowserOutputObservation)
        assert not obs.error
        assert 'File Upload Test' in obs.content

        # Parse the axtree to get the file input bid
        axtree_elements = parse_axtree_content(obs.content)
        # File inputs often show up as buttons in axtree, try multiple strategies
        file_input_bid = (
            find_element_by_text(axtree_elements, 'Choose File')
            or find_element_by_text(axtree_elements, 'No file chosen')
            or find_element_by_text(axtree_elements, 'Browse')
            or find_element_by_text(axtree_elements, 'file')
            or find_element_by_id(axtree_elements, 'file-input')
        )

        # Also look for button near the file input (Upload File button)
        upload_button_bid = find_element_by_text(axtree_elements, 'Upload File')

        # Test upload_file action with real bid
        assert file_input_bid is not None, (
            f'Could not find file input element in axtree. Available elements: {dict(list(axtree_elements.items())[:10])}'
        )

        action_browse = BrowseInteractiveAction(
            browser_actions=f'upload_file("{file_input_bid}", "/workspace/upload_test.txt")',
            return_axtree=True,
        )
        logger.info(action_browse, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_browse)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        assert isinstance(obs, BrowserOutputObservation)
        assert not obs.error, (
            f'File upload action failed: {obs.last_browser_action_error}'
        )

        # Verify the file input now shows the selected file
        updated_axtree_elements = parse_axtree_content(obs.content)
        assert file_input_bid in updated_axtree_elements, (
            f'File input element {file_input_bid} should be present in updated axtree. Available elements: {list(updated_axtree_elements.keys())[:10]}'
        )
        file_input_desc = updated_axtree_elements[file_input_bid]
        # File inputs typically show the filename when a file is selected
        assert (
            'upload_test.txt' in file_input_desc
            or 'upload_test' in file_input_desc
            or 'txt' in file_input_desc
        ), f'File input should show selected file but description is: {file_input_desc}'

        # Test clicking the upload button to trigger the JavaScript function
        if upload_button_bid:
            action_browse = BrowseInteractiveAction(
                browser_actions=f'click("{upload_button_bid}")',
                return_axtree=True,
            )
            logger.info(action_browse, extra={'msg_type': 'ACTION'})
            obs = runtime.run_action(action_browse)
            logger.info(obs, extra={'msg_type': 'OBSERVATION'})

            assert isinstance(obs, BrowserOutputObservation)
            assert not obs.error, (
                f'Upload button click failed: {obs.last_browser_action_error}'
            )

            # Check if the JavaScript function executed and updated the result div
            final_axtree_elements = parse_axtree_content(obs.content)
            # Look for the result text that should be set by JavaScript
            result_found = any(
                'File selected:' in desc or 'upload_test.txt' in desc
                for desc in final_axtree_elements.values()
            )
            assert result_found, (
                f'JavaScript upload handler should have updated the page but no result found in: {dict(list(final_axtree_elements.items())[:10])}'
            )

        # Clean up
        action_cmd = CmdRunAction(command='pkill -f "python3 -m http.server" || true')
        logger.info(action_cmd, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_cmd)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

    finally:
        _close_test_runtime(runtime)
def test_download_file(temp_dir, runtime_cls, run_as_openhands, dynamic_port):
    """Test downloading a file using the browser."""
    runtime, config = _load_runtime(
        temp_dir, runtime_cls, run_as_openhands, enable_browser=True
    )
    try:
        # Minimal PDF content for testing
        pdf_content = b"""%PDF-1.4
        1 0 obj

        /Type /Catalog
        /Pages 2 0 R
        >>
        endobj
        2 0 obj

        /Type /Pages
        /Kids [3 0 R]
        /Count 1
        >>
        endobj
        3 0 obj

        /Type /Page
        /Parent 2 0 R
        /MediaBox [0 0 612 792]
        >>
        endobj
        xref
        0 4
        0000000000 65535 f
        0000000010 00000 n
        0000000053 00000 n
        0000000125 00000 n
        trailer

        /Size 4
        /Root 1 0 R
        >>
        startxref
        212
        %%EOF"""

        test_file_name = 'test_download.pdf'
        test_file_path = os.path.join(temp_dir, test_file_name)
        with open(test_file_path, 'wb') as f:
            f.write(pdf_content)

        # Copy the file to the sandbox
        sandbox_dir = config.workspace_mount_path_in_sandbox
        runtime.copy_to(test_file_path, sandbox_dir)

        # Create a simple HTML page with a download link
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Download Test</title>
        </head>
        <body>
            <h1>Download Test Page</h1>
            <p>Click the link below to download the test file:</p>
            <a href="/{test_file_name}" download="{test_file_name}" id="download-link">Download Test File</a>
        </body>
        </html>
        """

        html_file_path = os.path.join(temp_dir, 'download_test.html')
        with open(html_file_path, 'w') as f:
            f.write(html_content)

        # Copy the HTML file to the sandbox
        runtime.copy_to(html_file_path, sandbox_dir)

        # Verify the files exist in the sandbox
        action_cmd = CmdRunAction(command='ls -alh')
        logger.info(action_cmd, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_cmd)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert isinstance(obs, CmdOutputObservation)
        assert obs.exit_code == 0
        assert test_file_name in obs.content
        assert 'download_test.html' in obs.content

        # Ensure downloads directory exists
        action_cmd = CmdRunAction(command='mkdir -p /workspace/.downloads')
        logger.info(action_cmd, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_cmd)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert obs.exit_code == 0

        # Start HTTP server
        action_cmd = CmdRunAction(
            command=f'python3 -m http.server {dynamic_port} > server.log 2>&1 &'
        )
        logger.info(action_cmd, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_cmd)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert isinstance(obs, CmdOutputObservation)
        assert obs.exit_code == 0

        # Wait for server to start
        action_cmd = CmdRunAction(command='sleep 2')
        logger.info(action_cmd, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_cmd)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        # Browse to the HTML page
        action_browse = BrowseURLAction(url=f'http://localhost:{dynamic_port}/')
        logger.info(action_browse, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_browse)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        # Verify the browser observation
        assert isinstance(obs, BrowserOutputObservation)
        assert f'http://localhost:{dynamic_port}/download_test.html' in obs.url
        assert not obs.error
        assert 'Download Test Page' in obs.content

        # Go to the PDF file url directly - this should trigger download
        file_url = f'http://localhost:{dynamic_port}/{test_file_name}'
        action_browse = BrowseInteractiveAction(
            browser_actions=f'goto("{file_url}")',
        )
        logger.info(action_browse, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_browse)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        # Verify the browser observation after navigating to PDF file
        downloaded_file_name = 'file_1.pdf'
        assert isinstance(obs, FileDownloadObservation)
        assert 'Location of downloaded file:' in str(obs)
        assert downloaded_file_name in str(obs)  # File is renamed

        # Wait for download to complete
        action_cmd = CmdRunAction(command='sleep 3')
        logger.info(action_cmd, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_cmd)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        # Check if the file was downloaded
        action_cmd = CmdRunAction(command='ls -la /workspace')
        logger.info(action_cmd, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_cmd)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert isinstance(obs, CmdOutputObservation)
        assert obs.exit_code == 0
        assert downloaded_file_name in obs.content

        # Clean up
        action_cmd = CmdRunAction(command='pkill -f "python3 -m http.server" || true')
        logger.info(action_cmd, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_cmd)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        action_cmd = CmdRunAction(command='rm -f server.log')
        logger.info(action_cmd, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_cmd)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
    finally:
        _close_test_runtime(runtime)
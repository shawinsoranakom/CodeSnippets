def test_read_pdf_browse(temp_dir, runtime_cls, run_as_openhands):
    runtime, config = _load_runtime(
        temp_dir, runtime_cls, run_as_openhands, enable_browser=True
    )
    try:
        # Create a PDF file using reportlab in the host environment
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas

        pdf_path = os.path.join(temp_dir, 'test_document.pdf')
        pdf_content = 'This is test content for PDF reading test'

        c = canvas.Canvas(pdf_path, pagesize=letter)
        # Add more content to make the PDF more robust
        c.drawString(100, 750, pdf_content)
        c.drawString(100, 700, 'Additional line for PDF structure')
        c.drawString(100, 650, 'Third line to ensure valid PDF')
        # Explicitly set PDF version and ensure proper structure
        c.setPageCompression(0)  # Disable compression for simpler structure
        c.save()

        # Copy the PDF to the sandbox
        sandbox_dir = config.workspace_mount_path_in_sandbox
        runtime.copy_to(pdf_path, sandbox_dir)

        # Start HTTP server
        action_cmd = CmdRunAction(command='ls -alh')
        logger.info(action_cmd, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_cmd)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert isinstance(obs, CmdOutputObservation)
        assert obs.exit_code == 0
        assert 'test_document.pdf' in obs.content

        # Get server url
        action_cmd = CmdRunAction(command='cat /tmp/oh-server-url')
        logger.info(action_cmd, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_cmd)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert obs.exit_code == 0
        server_url = obs.content.strip()

        # Browse to the PDF file
        pdf_url = f'{server_url}/view?path=/workspace/test_document.pdf'
        action_browse = BrowseInteractiveAction(
            browser_actions=f'goto("{pdf_url}")', return_axtree=False
        )
        logger.info(action_browse, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_browse)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        # Verify the browser observation
        assert isinstance(obs, BrowserOutputObservation)
        observation_text = str(obs)
        assert '[Action executed successfully.]' in observation_text
        assert 'Canvas' in observation_text
        assert (
            'Screenshot saved to: /workspace/.browser_screenshots/screenshot_'
            in observation_text
        )

        # Check the /workspace/.browser_screenshots folder
        action_cmd = CmdRunAction(command='ls /workspace/.browser_screenshots')
        logger.info(action_cmd, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_cmd)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert isinstance(obs, CmdOutputObservation)
        assert obs.exit_code == 0
        assert 'screenshot_' in obs.content
        assert '.png' in obs.content
    finally:
        _close_test_runtime(runtime)
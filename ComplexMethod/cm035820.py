def test_read_png_browse(temp_dir, runtime_cls, run_as_openhands):
    runtime, config = _load_runtime(
        temp_dir, runtime_cls, run_as_openhands, enable_browser=True
    )
    try:
        # Create a PNG file using PIL in the host environment
        from PIL import Image, ImageDraw

        png_path = os.path.join(temp_dir, 'test_image.png')
        # Create a simple image with text
        img = Image.new('RGB', (400, 200), color=(255, 255, 255))
        d = ImageDraw.Draw(img)
        text = 'This is a test PNG image'
        d.text((20, 80), text, fill=(0, 0, 0))
        img.save(png_path)

        # Copy the PNG to the sandbox
        sandbox_dir = config.workspace_mount_path_in_sandbox
        runtime.copy_to(png_path, sandbox_dir)

        # Verify the file exists in the sandbox
        action_cmd = CmdRunAction(command='ls -alh')
        logger.info(action_cmd, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_cmd)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert isinstance(obs, CmdOutputObservation)
        assert obs.exit_code == 0
        assert 'test_image.png' in obs.content

        # Get server url
        action_cmd = CmdRunAction(command='cat /tmp/oh-server-url')
        logger.info(action_cmd, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_cmd)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})
        assert obs.exit_code == 0
        server_url = obs.content.strip()

        # Browse to the PNG file
        png_url = f'{server_url}/view?path=/workspace/test_image.png'
        action_browse = BrowseInteractiveAction(
            browser_actions=f'goto("{png_url}")', return_axtree=False
        )
        logger.info(action_browse, extra={'msg_type': 'ACTION'})
        obs = runtime.run_action(action_browse)
        logger.info(obs, extra={'msg_type': 'OBSERVATION'})

        # Verify the browser observation
        assert isinstance(obs, BrowserOutputObservation)
        observation_text = str(obs)
        assert '[Action executed successfully.]' in observation_text
        assert 'File Viewer - test_image.png' in observation_text
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
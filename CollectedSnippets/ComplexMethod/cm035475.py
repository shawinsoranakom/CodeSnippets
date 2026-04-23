def check_dependencies(code_repo_path: str, check_browser: bool) -> None:
    ERROR_MESSAGE = 'Please follow the instructions in https://github.com/OpenHands/OpenHands/blob/main/Development.md to install OpenHands.'
    if not os.path.exists(code_repo_path):
        raise ValueError(
            f'Code repo path {code_repo_path} does not exist. ' + ERROR_MESSAGE
        )
    # Check jupyter is installed
    logger.debug('Checking dependencies: Jupyter')
    output = subprocess.check_output(
        [sys.executable, '-m', 'jupyter', '--version'],
        text=True,
        cwd=code_repo_path,
    )
    logger.debug(f'Jupyter output: {output}')
    if 'jupyter' not in output.lower():
        raise ValueError('Jupyter is not properly installed. ' + ERROR_MESSAGE)

    # Check libtmux is installed (skip on Windows)
    if sys.platform != 'win32':
        logger.debug('Checking dependencies: libtmux')
        import libtmux

        server = libtmux.Server()
        try:
            session = server.new_session(session_name='test-session')
        except Exception:
            raise ValueError('tmux is not properly installed or available on the path.')
        pane = session.active_pane

        if pane:
            pane.send_keys('echo "test"')
            pane_output = '\n'.join(pane.cmd('capture-pane', '-p').stdout)
        else:
            pane_output = ''
        session.kill()
        if 'test' not in pane_output:
            raise ValueError('libtmux is not properly installed. ' + ERROR_MESSAGE)

    if check_browser:
        logger.debug('Checking dependencies: browser')
        from openhands.runtime.browser.browser_env import BrowserEnv

        browser = BrowserEnv()
        browser.close()
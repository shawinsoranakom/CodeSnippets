async def get_nodriver(
    proxy: str = None,
    user_data_dir="nodriver",
    timeout: int = 300,
    browser_executable_path: str = None,
    **kwargs
) -> tuple[Browser, Callable]:
    if not has_nodriver:
        raise MissingRequirementsError(
            'Install "zendriver" and "platformdirs" package | pip install -U zendriver platformdirs')
    user_data_dir = user_config_dir(f"g4f-{user_data_dir}") if user_data_dir and has_platformdirs else None
    if browser_executable_path is None:
        browser_executable_path = BrowserConfig.executable_path
    if browser_executable_path is None:
        try:
            browser_executable_path = find_executable()
        except FileNotFoundError:
            # Default to Edge if Chrome is not available.
            browser_executable_path = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe"
            if not os.path.exists(browser_executable_path):
                # Default to Chromium on Linux systems.
                browser_executable_path = "/data/data/com.termux/files/usr/bin/chromium-browser"
                if not os.path.exists(browser_executable_path):
                    browser_executable_path = None
    debug.log(f"Browser executable path: {browser_executable_path}")
    lock_file = Path(get_cookies_dir()) / ".browser_is_open"
    if user_data_dir:
        lock_file.parent.mkdir(exist_ok=True)
        # Implement a short delay (milliseconds) to prevent race conditions.
        await asyncio.sleep(0.1 * random.randint(0, 50))
        if lock_file.exists():
            opend_at = float(lock_file.read_text())
            time_open = time.time() - opend_at
            if timeout * 2 > time_open:
                debug.log(f"Nodriver: Browser is already in use since {time_open} secs.")
                debug.log("Lock file:", lock_file)
                for idx in range(timeout):
                    if lock_file.exists():
                        await asyncio.sleep(1)
                    else:
                        break
                    if idx == timeout - 1:
                        debug.log("Timeout reached, nodriver is still in use.")
                        raise TimeoutError("Nodriver is already in use, please try again later.")
            else:
                debug.log(f"Nodriver: Browser was opened {time_open} secs ago, closing it.")
                await BrowserConfig.stop_browser()
                lock_file.unlink(missing_ok=True)
        lock_file.write_text(str(time.time()))
        debug.log(f"Open nodriver with user_dir: {user_data_dir}")
    try:
        browser_args = kwargs.pop("browser_args", None) or ["--no-sandbox"]

        if BrowserConfig.port:
            browser_executable_path = "/bin/google-chrome"
        browser = await nodriver.start(
            user_data_dir=user_data_dir,
            browser_args=[*browser_args, f"--proxy-server={proxy}"] if proxy else browser_args,
            browser_executable_path=browser_executable_path,
            port=BrowserConfig.port,
            host=BrowserConfig.host,
            connection_timeout=BrowserConfig.connection_timeout,
            **kwargs
        )
    except FileNotFoundError as e:
        raise MissingRequirementsError(e)

    async def on_stop():
        try:
            if BrowserConfig.port is None and browser.connection:
                await browser.stop()
        except Exception:
            pass
        finally:
            if user_data_dir:
                lock_file.unlink(missing_ok=True)

    BrowserConfig.stop_browser = on_stop
    return browser, on_stop
async def get_args_from_nodriver(
    url: str,
    proxy: str = None,
    timeout: int = 120,
    wait_for: str = None,
    callback: callable = None,
    cookies: Cookies = None,
    browser: Browser = None,
    user_data_dir: str = "nodriver",
    browser_args: list = None,
    clear_cookies_except:list[str]=None,
) -> dict:
    if clear_cookies_except is None:
        clear_cookies_except = []
    if browser is None:
        browser, stop_browser = await get_nodriver(proxy=proxy, timeout=timeout, user_data_dir=user_data_dir, browser_args=browser_args)
    else:
        async def stop_browser():
            pass
    try:
        if clear_cookies_except:
            debug.log(f"Clear Cookies for url: {url}")
            await clear_cookies_for_url(browser, url)

        debug.log(f"Open nodriver with url: {url}")
        if cookies is None:
            cookies = {}
        else:
            domain = urlparse(url).netloc
            await browser.cookies.set_all(get_cookie_params_from_dict(cookies, url=url, domain=domain))
        page = await browser.get(url)
        user_agent = await page.evaluate("window.navigator.userAgent", return_by_value=True)
        while not await page.evaluate("!!document.querySelector('body:not(.no-js)')"):
            await asyncio.sleep(1)
        if wait_for is not None:
            await page.wait_for(wait_for, timeout=timeout)
        if callback is not None:
            await callback(page)
        for c in await asyncio.wait_for(page.send(nodriver.cdp.network.get_cookies([url])), timeout=timeout):
            cookies[c.name] = c.value
        await stop_browser()
        return {
            "impersonate": "chrome",
            "cookies": cookies,
            "headers": {
                **DEFAULT_HEADERS,
                "user-agent": user_agent,
                "referer": f"{url.rstrip('/')}/",
            },
            "proxy": proxy,
        }
    except Exception:
        await stop_browser()
        raise
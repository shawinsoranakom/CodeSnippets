async def on_auth_async(cls, proxy: str = None, **kwargs) -> AsyncIterator:
        auth_result = AuthResult(headers=DEFAULT_HEADERS, impersonate="chrome")
        auth_result.headers["referer"] = cls.url + "/"
        browser, stop_browser = await get_nodriver(proxy=proxy)
        yield RequestLogin(cls.__name__, os.environ.get("G4F_LOGIN_URL") or "")
        try:
            page = await browser.get(cls.url)
            has_headers = False
            def on_request(event: nodriver.cdp.network.RequestWillBeSent, page=None):
                nonlocal has_headers
                if event.request.url.startswith(cls.conversation_url + "/new"):
                    for key, value in event.request.headers.items():
                        auth_result.headers[key.lower()] = value
                    has_headers = True
            await page.send(nodriver.cdp.network.enable())
            page.add_handler(nodriver.cdp.network.RequestWillBeSent, on_request)
            await page.reload()
            auth_result.headers["user-agent"] = await page.evaluate("window.navigator.userAgent", return_by_value=True)
            while True:
                if has_headers:
                    break
                input_element = None
                try:
                    input_element = await page.select("div.ProseMirror", 2)
                except Exception:
                    pass
                if not input_element:
                    try:
                        input_element = await page.select("textarea", 180)
                    except Exception:
                        pass
                if input_element:
                    try:
                        await input_element.click()
                        await input_element.send_keys("Hello")
                        await asyncio.sleep(0.5)
                        submit_btn = await page.select("button[type='submit']", 2)
                        if submit_btn:
                            await submit_btn.click()
                    except Exception:
                        pass
                await asyncio.sleep(1)
            auth_result.cookies = {}
            for c in await page.send(nodriver.cdp.network.get_cookies([cls.url])):
                auth_result.cookies[c.name] = c.value
            await page.close()
        finally:
            await stop_browser()
        yield auth_result
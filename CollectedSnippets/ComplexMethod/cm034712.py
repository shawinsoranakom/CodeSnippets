async def nodriver_auth(cls, proxy: str = None):
        async with get_nodriver_session(proxy=proxy) as browser:
            page = await browser.get(cls.url)

            def on_request(event: nodriver.cdp.network.RequestWillBeSent, page=None):
                if not hasattr(event, "request"):
                    return
                if event.request.url == start_url or event.request.url.startswith(conversation_url):
                    if cls.request_config.headers is None:
                        cls.request_config.headers = {}
                    for key, value in event.request.headers.items():
                        cls.request_config.headers[key.lower()] = value
                elif event.request.url in (backend_url, backend_anon_url, prepare_url):
                    if "OpenAI-Sentinel-Proof-Token" in event.request.headers:
                        cls.request_config.proof_token = json.loads(base64.b64decode(
                            event.request.headers["OpenAI-Sentinel-Proof-Token"].split("gAAAAAB", 1)[-1].split("~")[
                                0].encode()
                        ).decode())
                    if "OpenAI-Sentinel-Turnstile-Token" in event.request.headers:
                        cls.request_config.turnstile_token = event.request.headers["OpenAI-Sentinel-Turnstile-Token"]
                    if "Authorization" in event.request.headers:
                        cls._api_key = event.request.headers["Authorization"].split()[-1]
                elif event.request.url == arkose_url:
                    cls.request_config.arkose_request = arkReq(
                        arkURL=event.request.url,
                        arkBx=None,
                        arkHeader=event.request.headers,
                        arkBody=event.request.post_data,
                        userAgent=event.request.headers.get("User-Agent")
                    )

            await page.send(nodriver.cdp.network.enable())
            page.add_handler(nodriver.cdp.network.RequestWillBeSent, on_request)
            await page.reload()
            user_agent = await page.evaluate("window.navigator.userAgent", return_by_value=True)
            debug.log(f"OpenaiChat: User-Agent: {user_agent}")
            for _ in range(3):
                try:
                    if cls.needs_auth:
                        try:
                            await page.select('[data-testid="accounts-profile-button"]', 300)
                        except TimeoutError:
                            continue
                    try:
                        textarea = await page.select("#prompt-textarea", 300)
                        await textarea.send_keys("Hello")
                        await asyncio.sleep(1)
                    except TimeoutError:
                        continue
                except nodriver.core.connection.ProtocolException:
                    continue
                break
            try:
                button = await page.select("[data-testid=\"send-button\"]")
                await button.click()
                debug.log("OpenaiChat: 'Hello' sended")
            except TimeoutError:
                pass
            while True:
                body = await page.evaluate("JSON.stringify(window.__remixContext)", return_by_value=True)
                if hasattr(body, "value"):
                    body = body.value
                if body:
                    match = re.search(r'"accessToken":"(.+?)"', body)
                    if match:
                        cls._api_key = match.group(1)
                        break
                if cls._api_key is not None or not cls.needs_auth:
                    break
                await asyncio.sleep(1)
                debug.log("OpenaiChat: Waiting for access token...")
            debug.log(f"OpenaiChat: Access token: {'False' if cls._api_key is None else cls._api_key[:12] + '...'}")
            #while True:
            #    if cls.request_config.proof_token:
            #        break
            #    await asyncio.sleep(1)
            #    debug.log("OpenaiChat: Waiting for proof token...")
            #debug.log(f"OpenaiChat: Proof token: Yes")
            cls.request_config.data_build = await page.evaluate("document.documentElement.getAttribute('data-build')")
            cls.request_config.cookies = await page.send(get_cookies([cls.url]))
            await page.close()
            cls._create_request_args(cls.request_config.cookies, cls.request_config.headers, user_agent=user_agent)
            cls._set_api_key(cls._api_key)
            debug.log(f"OpenaiChat: Sleep 10s")
            await asyncio.sleep(10)
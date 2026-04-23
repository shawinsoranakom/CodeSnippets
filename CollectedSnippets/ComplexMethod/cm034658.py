async def get_access_token_and_cookies(url: str, proxy: str = None, needs_auth: bool = False):
    browser, stop_browser = await get_nodriver(proxy=proxy)
    try:
        page = await browser.get(url)
        access_token = None
        useridentitytype = None
        while access_token is None:
            for _ in range(2):
                await asyncio.sleep(3)
                access_token = await page.evaluate("""
                    (() => {
                        for (var i = 0; i < localStorage.length; i++) {
                            try {
                                const key = localStorage.key(i);
                                const item = JSON.parse(localStorage.getItem(key));
                                if (item?.body?.access_token) {
                                    return ["" + item?.body?.access_token, "google"];
                                } else if (key.includes("chatai")) {
                                    return "" + item.secret;
                                }
                            } catch(e) {}
                        }
                    })()
                """)
                if access_token is None:
                    await asyncio.sleep(1)
                    continue
                if isinstance(access_token, list):
                    access_token, useridentitytype = access_token
                access_token = access_token.get("value") if isinstance(access_token, dict) else access_token
                useridentitytype = useridentitytype.get("value") if isinstance(useridentitytype, dict) else None
                debug.log(f"Got access token: {access_token[:10]}..., useridentitytype: {useridentitytype}")
                break
            if not needs_auth:
                debug.log("No access token found, but authentication not required.")
                break
        if not needs_auth:
            try:
                textarea = await page.select("textarea")
            except TimeoutError:
                textarea = None
            if textarea is not None:
                debug.log("Filling textarea to generate anon cookie.")
                await textarea.send_keys("Hello")
                await asyncio.sleep(1)
                try:
                    button = await page.select("[data-testid=\"submit-button\"]")
                except TimeoutError:
                    button = None
                if button:
                    debug.log("Clicking submit button to generate anon cookie.")
                    await button.click()
                    try:
                        turnstile = await page.select('#cf-turnstile')
                    except TimeoutError:
                        turnstile = None
                    if turnstile:
                        debug.log("Found Element: 'cf-turnstile'")
                        await asyncio.sleep(3)
                        await click_trunstile(page)
        cookies = {}
        while not access_token and Copilot.anon_cookie_name not in cookies:
            await asyncio.sleep(2)
            cookies = {c.name: c.value for c in await page.send(nodriver.cdp.network.get_cookies([url]))}
            if not needs_auth and Copilot.anon_cookie_name in cookies:
                break
            elif needs_auth and next(filter(lambda x: "auth0" in x, cookies), None):
                break
        await stop_browser()
        return access_token, useridentitytype, cookies
    finally:
        await stop_browser()
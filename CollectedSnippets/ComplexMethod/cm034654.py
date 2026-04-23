async def callback(page):
            cls.captchaToken = None
            def on_request(event: nodriver.cdp.network.RequestWillBeSent, page=None):
                if event.request.url != cls.api_endpoint:
                    return
                if not event.request.post_data:
                    return
                cls.captchaToken = json.loads(event.request.post_data).get("captchaToken")
            await page.send(nodriver.cdp.network.enable())
            page.add_handler(nodriver.cdp.network.RequestWillBeSent, on_request)
            button = await page.find("我已知晓")
            if button:
                await button.click()
            else:
                debug.error("No 'Agree' button found.")
            for _ in range(3):
                await asyncio.sleep(1)
                for _ in range(300):
                    modal = await page.find("Verifying...")
                    if not modal:
                        break
                    debug.log("EasyChat: Waiting for captcha verification...")
                    await asyncio.sleep(1)
                if cls.captchaToken:
                    debug.log("EasyChat: Captcha token found, proceeding.")
                    break
                textarea = await page.select("[contenteditable=\"true\"]", 180)
                if textarea is not None:
                    await textarea.send_keys("Hello")
                    await asyncio.sleep(1)
                    button = await page.select("button[class*='chat_chat-input-send']")
                    if button:
                        await button.click()
            for _ in range(300):
                await asyncio.sleep(1)
                if cls.captchaToken:
                    break
            cls.guestId = await page.evaluate('"" + JSON.parse(localStorage.getItem("user-info") || "{}")?.state?.guestId')
            await asyncio.sleep(3)
async def callback(page: nodriver.Tab):
            try:
                button = await page.find("Accept Cookies")
            except TimeoutError:
                button = None
            if button:
                await button.click()
            else:
                debug.log("No 'Accept Cookies' button found, skipping.")
            await asyncio.sleep(1)
            try:
                textarea = await page.select('textarea[name="message"]')
            except TimeoutError:
                textarea = None
            if textarea:
                await textarea.send_keys("Hello")
            # await asyncio.sleep(1)
            # button = await page.select('button[type="submit"]')
            # if button:
            #     await button.click()
            # button = await page.find("Agree")
            # if button:
            #     await button.click()
            # else:
            #     debug.log("No 'Agree' button found, skipping.")
            # await asyncio.sleep(1)
            # try:
            #     element = await page.select('[style="display: grid;"]')
            # except TimeoutError:
            #     element = None
            # if element:
            #     await click_trunstile(page, 'document.querySelector(\'[style="display: grid;"]\')')
            while not await page.evaluate('document.cookie.indexOf("arena-auth-prod-v1") >= 0'):
                debug.log("No authentication cookie found, waiting for authenticate.")
                #await page.select('#cf-turnstile', 300)
                #debug.log("Found Element: 'cf-turnstile'")
                await asyncio.sleep(3)
                #await click_trunstile(page)
            while not await page.evaluate('document.cookie.indexOf("arena-auth-prod-v1") >= 0'):
                await asyncio.sleep(1)
            while not await page.evaluate('!!document.querySelector(\'textarea\')'):
                await asyncio.sleep(1)
            while not await page.evaluate('window.grecaptcha && window.grecaptcha.enterprise'):
                await asyncio.sleep(1)
            captcha = await page.evaluate(
                """window.grecaptcha.enterprise.execute('6Led_uYrAAAAAKjxDIF58fgFtX3t8loNAK85bW9I',  { action: 'chat_submit' }  );""",
                await_promise=True)
            grecaptcha.append(captcha)
            debug.log("Obtained grecaptcha token.")
            html = await page.get_content()
            await cls.__load_actions(html)
async def ask_stream(
        self,
        prompt: str,
        wss_link: str,
        conversation_style: CONVERSATION_STYLE_TYPE = None,
        raw: bool = False,
        options: dict = None,
        webpage_context=None,
        search_result: bool = False,
    ) -> Generator[str, None, None]:
        """
        Ask a question to the bot
        """
        req_header = HEADERS
        if self.cookies is not None:
            ws_cookies = []
            for cookie in self.cookies:
                ws_cookies.append(f"{cookie['name']}={cookie['value']}")
            req_header.update(
                {
                    "Cookie": ";".join(ws_cookies),
                }
            )

        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)

        if self.wss and not self.wss.closed:
            await self.wss.close()
        # Check if websocket is closed
        self.wss = await self.session.ws_connect(
            wss_link,
            headers=req_header,
            ssl=ssl_context,
            proxy=self.proxy,
            autoping=False,
        )
        await self._initial_handshake()
        if self.request.invocation_id == 0:
            # Construct a ChatHub request
            self.request.update(
                prompt=prompt,
                conversation_style=conversation_style,
                options=options,
                webpage_context=webpage_context,
                search_result=search_result,
            )
        else:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://sydney.bing.com/sydney/UpdateConversation/",
                    json={
                        "messages": [
                            {
                                "author": "user",
                                "description": webpage_context,
                                "contextType": "WebPage",
                                "messageType": "Context",
                            },
                        ],
                        "conversationId": self.request.conversation_id,
                        "source": "cib",
                        "traceId": _get_ran_hex(32),
                        "participant": {"id": self.request.client_id},
                        "conversationSignature": self.request.conversation_signature,
                    },
                )
            if response.status_code != 200:
                print(f"Status code: {response.status_code}")
                print(response.text)
                print(response.url)
                raise Exception("Update web page context failed")
            # Construct a ChatHub request
            self.request.update(
                prompt=prompt,
                conversation_style=conversation_style,
                options=options,
            )
        # Send request
        await self.wss.send_str(_append_identifier(self.request.struct))
        final = False
        draw = False
        resp_txt = ""
        result_text = ""
        resp_txt_no_link = ""
        while not final:
            msg = await self.wss.receive()
            try:
                objects = msg.data.split(DELIMITER)
            except:
                continue

            for obj in objects:
                if obj is None or not obj:
                    continue
                response = json.loads(obj)
                if response.get("type") != 2 and raw:
                    yield False, response
                elif response.get("type") == 1 and response["arguments"][0].get(
                    "messages",
                ):
                    if not draw:
                        if (
                            response["arguments"][0]["messages"][0].get("messageType")
                            == "GenerateContentQuery"
                        ):
                            async with ImageGenAsync("", True) as image_generator:
                                images = await image_generator.get_images(
                                    response["arguments"][0]["messages"][0]["text"],
                                )
                            for i, image in enumerate(images):
                                resp_txt = resp_txt + f"\n![image{i}]({image})"
                            draw = True
                        if (
                            response["arguments"][0]["messages"][0]["contentOrigin"]
                            != "Apology"
                        ) and not draw:
                            resp_txt = result_text + response["arguments"][0][
                                "messages"
                            ][0]["adaptiveCards"][0]["body"][0].get("text", "")
                            resp_txt_no_link = result_text + response["arguments"][0][
                                "messages"
                            ][0].get("text", "")
                            if response["arguments"][0]["messages"][0].get(
                                "messageType",
                            ):
                                resp_txt = (
                                    resp_txt
                                    + response["arguments"][0]["messages"][0][
                                        "adaptiveCards"
                                    ][0]["body"][0]["inlines"][0].get("text")
                                    + "\n"
                                )
                                result_text = (
                                    result_text
                                    + response["arguments"][0]["messages"][0][
                                        "adaptiveCards"
                                    ][0]["body"][0]["inlines"][0].get("text")
                                    + "\n"
                                )
                        yield False, resp_txt

                elif response.get("type") == 2:
                    if response["item"]["result"].get("error"):
                        await self.close()
                        raise Exception(
                            f"{response['item']['result']['value']}: {response['item']['result']['message']}",
                        )
                    if draw:
                        cache = response["item"]["messages"][1]["adaptiveCards"][0][
                            "body"
                        ][0]["text"]
                        response["item"]["messages"][1]["adaptiveCards"][0]["body"][0][
                            "text"
                        ] = (cache + resp_txt)
                    if (
                        response["item"]["messages"][-1]["contentOrigin"] == "Apology"
                        and resp_txt
                    ):
                        response["item"]["messages"][-1]["text"] = resp_txt_no_link
                        response["item"]["messages"][-1]["adaptiveCards"][0]["body"][0][
                            "text"
                        ] = resp_txt
                        print(
                            "Preserved the message from being deleted",
                            file=sys.stderr,
                        )
                    final = True
                    await self.close()
                    yield True, response
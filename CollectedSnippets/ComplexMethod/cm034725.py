async def prompt(self, message: str, cookies: Cookies = None) -> AsyncResult:
        if self.cookies is None:
            await self.update_cookies(cookies)
        if cookies is not None:
            self.access_token = None
        if self.access_token is None and cookies is None:
            await self.update_access_token()
        if self.access_token is None:
            url = "https://www.meta.ai/api/graphql/"
            payload = {"lsd": self.lsd, 'fb_dtsg': self.dtsg}
            headers = {'x-fb-lsd': self.lsd}
        else:
            url = "https://graph.meta.ai/graphql?locale=user"
            payload = {"access_token": self.access_token}
            headers = {}
        headers = {
            'content-type': 'application/x-www-form-urlencoded',
            'cookie': format_cookies(self.cookies),
            'origin': 'https://www.meta.ai',
            'referer': 'https://www.meta.ai/',
            'x-asbd-id': '129477',
            'x-fb-friendly-name': 'useAbraSendMessageMutation',
            **headers
        }
        payload = {
            **payload,
            'fb_api_caller_class': 'RelayModern',
            'fb_api_req_friendly_name': 'useAbraSendMessageMutation',
            "variables": json.dumps({
                "message": {"sensitive_string_value": message},
                "externalConversationId": str(uuid.uuid4()),
                "offlineThreadingId": generate_offline_threading_id(),
                "suggestedPromptIndex": None,
                "flashVideoRecapInput": {"images": []},
                "flashPreviewInput": None,
                "promptPrefix": None,
                "entrypoint": "ABRA__CHAT__TEXT",
                "icebreaker_type": "TEXT",
                "__relay_internal__pv__AbraDebugDevOnlyrelayprovider": False,
                "__relay_internal__pv__WebPixelRatiorelayprovider": 1,
            }),
            'server_timestamps': 'true',
            'doc_id': '7783822248314888'
        }
        async with self.session.post(url, headers=headers, data=payload) as response:
            await raise_for_status(response, "Fetch response failed")
            last_snippet_len = 0
            fetch_id = None
            async for line in response.content:
                if b"<h1>Something Went Wrong</h1>" in line:
                    raise ResponseError("Response: Something Went Wrong")
                try:
                    json_line = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if json_line.get("errors"):
                    raise RuntimeError("\n".join([error.get("message") for error in json_line.get("errors")]))
                bot_response_message = json_line.get("data", {}).get("node", {}).get("bot_response_message", {})
                streaming_state = bot_response_message.get("streaming_state")
                fetch_id = bot_response_message.get("fetch_id") or fetch_id
                if streaming_state in ("STREAMING", "OVERALL_DONE"):
                    imagine_card = bot_response_message.get("imagine_card")
                    if imagine_card is not None:
                        imagine_session = imagine_card.get("session")
                        if imagine_session is not None:
                            imagine_medias = imagine_session.get("media_sets", {}).pop().get("imagine_media")
                            if imagine_medias is not None:
                                image_class = ImageResponse if streaming_state == "OVERALL_DONE" else ImagePreview
                                yield image_class([media["uri"] for media in imagine_medias], imagine_medias[0]["prompt"])
                    snippet =  bot_response_message["snippet"]
                    new_snippet_len = len(snippet)
                    if new_snippet_len > last_snippet_len:
                        yield snippet[last_snippet_len:]
                        last_snippet_len = new_snippet_len
            #if last_streamed_response is None:
            #    if attempts > 3:
            #        raise Exception("MetaAI is having issues and was not able to respond (Server Error)")
            #    access_token = await self.get_access_token()
            #    return await self.prompt(message=message, attempts=attempts + 1)
            if fetch_id is not None:
                sources = await self.fetch_sources(fetch_id)
                if sources is not None:
                    yield sources
async def _summarize_page(
        self,
        question: str | None = None,
        cancellation_token: Optional[CancellationToken] = None,
    ) -> str:
        assert self._page is not None

        page_markdown: str = await self._playwright_controller.get_page_markdown(self._page)

        title: str = self._page.url
        try:
            title = await self._page.title()
        except Exception:
            pass

        # Take a screenshot and scale it
        screenshot = Image.open(io.BytesIO(await self._page.screenshot()))
        scaled_screenshot = screenshot.resize((self.MLM_WIDTH, self.MLM_HEIGHT))
        screenshot.close()
        ag_image = AGImage.from_pil(scaled_screenshot)

        # Prepare the system prompt
        messages: List[LLMMessage] = []
        messages.append(SystemMessage(content=WEB_SURFER_QA_SYSTEM_MESSAGE))
        prompt = WEB_SURFER_QA_PROMPT(title, question)
        # Grow the buffer (which is added to the prompt) until we overflow the context window or run out of lines
        buffer = ""
        # for line in re.split(r"([\r\n]+)", page_markdown):
        for line in page_markdown.splitlines():
            trial_message = UserMessage(
                content=prompt + buffer + line,
                source=self.name,
            )

            try:
                remaining = self._model_client.remaining_tokens(messages + [trial_message])
            except KeyError:
                # Use the default if the model isn't found
                remaining = DEFAULT_CONTEXT_SIZE - self._model_client.count_tokens(messages + [trial_message])

            if self._model_client.model_info["vision"] and remaining <= 0:
                break

            if self._model_client.model_info["vision"] and remaining <= self.SCREENSHOT_TOKENS:
                break

            buffer += line

        # Nothing to do
        buffer = buffer.strip()
        if len(buffer) == 0:
            return "Nothing to summarize."

        # Append the message
        if self._model_client.model_info["vision"]:
            # Multimodal
            messages.append(
                UserMessage(
                    content=[
                        prompt + buffer,
                        ag_image,
                    ],
                    source=self.name,
                )
            )
        else:
            # Text only
            messages.append(
                UserMessage(
                    content=prompt + buffer,
                    source=self.name,
                )
            )

        # Generate the response
        response = await self._model_client.create(messages, cancellation_token=cancellation_token)
        self.model_usage.append(response.usage)
        scaled_screenshot.close()
        assert isinstance(response.content, str)
        return response.content
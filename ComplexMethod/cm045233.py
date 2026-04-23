async def _execute_tool(
        self,
        message: List[FunctionCall],
        rects: Dict[str, InteractiveRegion],
        tool_names: str,
        cancellation_token: Optional[CancellationToken] = None,
    ) -> UserContent:
        # Execute the tool
        name = message[0].name
        args = json.loads(message[0].arguments)
        action_description = ""
        assert self._page is not None
        self.logger.info(
            WebSurferEvent(
                source=self.name,
                url=self._page.url,
                action=name,
                arguments=args,
                message=f"{name}( {json.dumps(args)} )",
            )
        )
        self.inner_messages.append(TextMessage(content=f"{name}( {json.dumps(args)} )", source=self.name))

        if name == "visit_url":
            url = args.get("url")
            action_description = f"I typed '{url}' into the browser address bar."
            # Check if the argument starts with a known protocol
            if url.startswith(("https://", "http://", "file://", "about:")):
                reset_prior_metadata, reset_last_download = await self._playwright_controller.visit_page(
                    self._page, url
                )
            # If the argument contains a space, treat it as a search query
            elif " " in url:
                reset_prior_metadata, reset_last_download = await self._playwright_controller.visit_page(
                    self._page, f"https://www.bing.com/search?q={quote_plus(url)}&FORM=QBLH"
                )
            # Otherwise, prefix with https://
            else:
                reset_prior_metadata, reset_last_download = await self._playwright_controller.visit_page(
                    self._page, "https://" + url
                )
            if reset_last_download and self._last_download is not None:
                self._last_download = None
            if reset_prior_metadata and self._prior_metadata_hash is not None:
                self._prior_metadata_hash = None
        elif name == "history_back":
            action_description = "I clicked the browser back button."
            await self._playwright_controller.back(self._page)

        elif name == "web_search":
            query = args.get("query")
            action_description = f"I typed '{query}' into the browser search bar."
            reset_prior_metadata, reset_last_download = await self._playwright_controller.visit_page(
                self._page, f"https://www.bing.com/search?q={quote_plus(query)}&FORM=QBLH"
            )
            if reset_last_download and self._last_download is not None:
                self._last_download = None
            if reset_prior_metadata and self._prior_metadata_hash is not None:
                self._prior_metadata_hash = None
        elif name == "scroll_up":
            action_description = "I scrolled up one page in the browser."
            await self._playwright_controller.page_up(self._page)
        elif name == "scroll_down":
            action_description = "I scrolled down one page in the browser."
            await self._playwright_controller.page_down(self._page)

        elif name == "click":
            target_id = str(args.get("target_id"))
            target_name = self._target_name(target_id, rects)
            if target_name:
                action_description = f"I clicked '{target_name}'."
            else:
                action_description = "I clicked the control."
            new_page_tentative = await self._playwright_controller.click_id(self._page, target_id)
            if new_page_tentative is not None:
                self._page = new_page_tentative
                self._prior_metadata_hash = None
                self.logger.info(
                    WebSurferEvent(
                        source=self.name,
                        url=self._page.url,
                        message="New tab or window.",
                    )
                )
        elif name == "input_text":
            input_field_id = str(args.get("input_field_id"))
            text_value = str(args.get("text_value"))
            input_field_name = self._target_name(input_field_id, rects)
            if input_field_name:
                action_description = f"I typed '{text_value}' into '{input_field_name}'."
            else:
                action_description = f"I input '{text_value}'."
            await self._playwright_controller.fill_id(self._page, input_field_id, text_value)

        elif name == "scroll_element_up":
            target_id = str(args.get("target_id"))
            target_name = self._target_name(target_id, rects)

            if target_name:
                action_description = f"I scrolled '{target_name}' up."
            else:
                action_description = "I scrolled the control up."

            await self._playwright_controller.scroll_id(self._page, target_id, "up")

        elif name == "scroll_element_down":
            target_id = str(args.get("target_id"))
            target_name = self._target_name(target_id, rects)

            if target_name:
                action_description = f"I scrolled '{target_name}' down."
            else:
                action_description = "I scrolled the control down."

            await self._playwright_controller.scroll_id(self._page, target_id, "down")

        elif name == "answer_question":
            question = str(args.get("question"))
            action_description = f"I answered the following question '{question}' based on the web page."
            # Do Q&A on the DOM. No need to take further action. Browser state does not change.
            return await self._summarize_page(question=question, cancellation_token=cancellation_token)
        elif name == "summarize_page":
            # Summarize the DOM. No need to take further action. Browser state does not change.
            action_description = "I summarized the current web page"
            return await self._summarize_page(cancellation_token=cancellation_token)

        elif name == "hover":
            target_id = str(args.get("target_id"))
            target_name = self._target_name(target_id, rects)
            if target_name:
                action_description = f"I hovered over '{target_name}'."
            else:
                action_description = "I hovered over the control."
            await self._playwright_controller.hover_id(self._page, target_id)

        elif name == "sleep":
            action_description = "I am waiting a short period of time before taking further action."
            await self._playwright_controller.sleep(self._page, 3)

        else:
            raise ValueError(f"Unknown tool '{name}'. Please choose from:\n\n{tool_names}")

        await self._page.wait_for_load_state()
        await self._playwright_controller.sleep(self._page, 3)

        # Handle downloads
        if self._last_download is not None and self.downloads_folder is not None:
            fname = os.path.join(self.downloads_folder, self._last_download.suggested_filename)
            await self._last_download.save_as(fname)  # type: ignore
            page_body = f"<html><head><title>Download Successful</title></head><body style=\"margin: 20px;\"><h1>Successfully downloaded '{self._last_download.suggested_filename}' to local path:<br><br>{fname}</h1></body></html>"
            await self._page.goto(
                "data:text/html;base64," + base64.b64encode(page_body.encode("utf-8")).decode("utf-8")
            )
            await self._page.wait_for_load_state()

        # Handle metadata
        page_metadata = json.dumps(await self._playwright_controller.get_page_metadata(self._page), indent=4)
        metadata_hash = hashlib.md5(page_metadata.encode("utf-8")).hexdigest()
        if metadata_hash != self._prior_metadata_hash:
            page_metadata = (
                "\n\nThe following metadata was extracted from the webpage:\n\n" + page_metadata.strip() + "\n"
            )
        else:
            page_metadata = ""
        self._prior_metadata_hash = metadata_hash

        new_screenshot = await self._page.screenshot()
        if self.to_save_screenshots:
            current_timestamp = "_" + int(time.time()).__str__()
            screenshot_png_name = "screenshot" + current_timestamp + ".png"

            async with aiofiles.open(os.path.join(self.debug_dir, screenshot_png_name), "wb") as file:  # type: ignore
                await file.write(new_screenshot)  # type: ignore
            self.logger.info(
                WebSurferEvent(
                    source=self.name,
                    url=self._page.url,
                    message="Screenshot: " + screenshot_png_name,
                )
            )

        # Return the complete observation
        state_description = "The " + await self._get_state_description()
        message_content = (
            f"{action_description}\n\n" + state_description + page_metadata + "\nHere is a screenshot of the page."
        )

        return [
            re.sub(r"(\n\s*){3,}", "\n\n", message_content),  # Removing blank lines
            AGImage.from_pil(PIL.Image.open(io.BytesIO(new_screenshot))),
        ]
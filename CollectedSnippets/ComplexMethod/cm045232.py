async def _generate_reply(self, cancellation_token: CancellationToken) -> UserContent:
        """Generates the actual reply. First calls the LLM to figure out which tool to use, then executes the tool."""

        # Lazy init, initialize the browser and the page on the first generate reply only
        if not self.did_lazy_init:
            await self._lazy_init()

        assert self._page is not None

        # Clone the messages, removing old screenshots
        history: List[LLMMessage] = remove_images(self._chat_history)

        # Split the history, removing the last message
        if len(history):
            user_request = history.pop()
        else:
            user_request = UserMessage(content="Empty request.", source="user")

        # Truncate the history for smaller models
        if self._model_client.model_info["family"] not in [
            ModelFamily.GPT_4O,
            ModelFamily.O1,
            ModelFamily.O3,
            ModelFamily.GPT_4,
            ModelFamily.GPT_35,
        ]:
            history = []

        # Ask the page for interactive elements, then prepare the state-of-mark screenshot
        rects = await self._playwright_controller.get_interactive_rects(self._page)
        viewport = await self._playwright_controller.get_visual_viewport(self._page)
        screenshot = await self._page.screenshot()
        som_screenshot, visible_rects, rects_above, rects_below = add_set_of_mark(screenshot, rects)

        if self.to_save_screenshots:
            current_timestamp = "_" + int(time.time()).__str__()
            screenshot_png_name = "screenshot_som" + current_timestamp + ".png"
            som_screenshot.save(os.path.join(self.debug_dir, screenshot_png_name))  # type: ignore
            self.logger.info(
                WebSurferEvent(
                    source=self.name,
                    url=self._page.url,
                    message="Screenshot: " + screenshot_png_name,
                )
            )
        # What tools are available?
        tools = self.default_tools.copy()

        # We can scroll up
        if viewport["pageTop"] > 5:
            tools.append(TOOL_SCROLL_UP)

        # Can scroll down
        if (viewport["pageTop"] + viewport["height"] + 5) < viewport["scrollHeight"]:
            tools.append(TOOL_SCROLL_DOWN)

        # Focus hint
        focused = await self._playwright_controller.get_focused_rect_id(self._page)
        focused_hint = ""
        if focused:
            name = self._target_name(focused, rects)
            if name:
                name = f"(and name '{name}') "
            else:
                name = ""

            role = "control"
            try:
                role = rects[focused]["role"]
            except KeyError:
                pass

            focused_hint = f"\nThe {role} with ID {focused} {name}currently has the input focus.\n\n"

        # Everything visible
        visible_targets = "\n".join(self._format_target_list(visible_rects, rects)) + "\n\n"

        # Everything else
        other_targets: List[str] = []
        other_targets.extend(self._format_target_list(rects_above, rects))
        other_targets.extend(self._format_target_list(rects_below, rects))

        if len(other_targets) > 0:
            if len(other_targets) > 30:
                other_targets = other_targets[0:30]
                other_targets.append("...")
            other_targets_str = (
                "Additional valid interaction targets include (but are not limited to):\n"
                + "\n".join(other_targets)
                + "\n\n"
            )
        else:
            other_targets_str = ""

        state_description = "Your " + await self._get_state_description()
        tool_names = "\n".join([t["name"] for t in tools])
        page_title = await self._page.title()

        prompt_message = None
        if self._model_client.model_info["vision"]:
            text_prompt = WEB_SURFER_TOOL_PROMPT_MM.format(
                state_description=state_description,
                visible_targets=visible_targets,
                other_targets_str=other_targets_str,
                focused_hint=focused_hint,
                tool_names=tool_names,
                title=page_title,
                url=self._page.url,
            ).strip()

            # Scale the screenshot for the MLM, and close the original
            scaled_screenshot = som_screenshot.resize((self.MLM_WIDTH, self.MLM_HEIGHT))
            som_screenshot.close()
            if self.to_save_screenshots:
                scaled_screenshot.save(os.path.join(self.debug_dir, "screenshot_scaled.png"))  # type: ignore

            # Create the message
            prompt_message = UserMessage(
                content=[re.sub(r"(\n\s*){3,}", "\n\n", text_prompt), AGImage.from_pil(scaled_screenshot)],
                source=self.name,
            )
        else:
            text_prompt = WEB_SURFER_TOOL_PROMPT_TEXT.format(
                state_description=state_description,
                visible_targets=visible_targets,
                other_targets_str=other_targets_str,
                focused_hint=focused_hint,
                tool_names=tool_names,
                title=page_title,
                url=self._page.url,
            ).strip()

            # Create the message
            prompt_message = UserMessage(content=re.sub(r"(\n\s*){3,}", "\n\n", text_prompt), source=self.name)

        history.append(prompt_message)
        history.append(user_request)

        # {history[-2].content if isinstance(history[-2].content, str) else history[-2].content[0]}
        # print(f"""
        # ================={len(history)}=================
        # {history[-2].content}
        # =====
        # {history[-1].content}
        # ===================================================
        # """)

        # Make the request
        response = await self._model_client.create(
            history, tools=tools, extra_create_args={"tool_choice": "auto"}, cancellation_token=cancellation_token
        )  # , "parallel_tool_calls": False})

        self.model_usage.append(response.usage)
        message = response.content
        self._last_download = None
        if isinstance(message, str):
            # Answer directly
            self.inner_messages.append(TextMessage(content=message, source=self.name))
            return message
        elif isinstance(message, list):
            # Take an action
            return await self._execute_tool(message, rects, tool_names, cancellation_token=cancellation_token)
        else:
            # Not sure what happened here
            raise AssertionError(f"Unknown response format '{message}'")
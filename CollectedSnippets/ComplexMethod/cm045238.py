async def _generate_reply(self, cancellation_token: CancellationToken) -> Tuple[bool, str]:
        history = self._chat_history[0:-1]
        last_message = self._chat_history[-1]
        assert isinstance(last_message, UserMessage)

        task_content = last_message.content  # the last message from the sender is the task

        assert self._browser is not None

        context_message = UserMessage(
            source="user",
            content=f"Your file viewer is currently open to the file or directory '{self._browser.page_title}' with path '{self._browser.path}'.",
        )

        task_message = UserMessage(
            source="user",
            content=task_content,
        )

        create_result = await self._model_client.create(
            messages=self._get_compatible_context(history + [context_message, task_message]),
            tools=[
                TOOL_OPEN_PATH,
                TOOL_PAGE_DOWN,
                TOOL_PAGE_UP,
                TOOL_FIND_NEXT,
                TOOL_FIND_ON_PAGE_CTRL_F,
            ],
            cancellation_token=cancellation_token,
        )

        response = create_result.content

        if isinstance(response, str):
            # Answer directly.
            return False, response

        elif isinstance(response, list) and all(isinstance(item, FunctionCall) for item in response):
            function_calls = response
            for function_call in function_calls:
                tool_name = function_call.name

                try:
                    arguments = json.loads(function_call.arguments)
                except json.JSONDecodeError as e:
                    error_str = f"File surfer encountered an error decoding JSON arguments: {e}"
                    return False, error_str

                if tool_name == "open_path":
                    path = arguments["path"]
                    self._browser.open_path(path)
                elif tool_name == "page_up":
                    self._browser.page_up()
                elif tool_name == "page_down":
                    self._browser.page_down()
                elif tool_name == "find_on_page_ctrl_f":
                    search_string = arguments["search_string"]
                    self._browser.find_on_page(search_string)
                elif tool_name == "find_next":
                    self._browser.find_next()
            header, content = self._get_browser_state()
            final_response = header.strip() + "\n=======================\n" + content
            return False, final_response

        final_response = "TERMINATE"
        return False, final_response
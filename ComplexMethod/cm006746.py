async def run_agent(
        self,
        agent: Runnable | BaseSingleActionAgent | BaseMultiActionAgent | AgentExecutor,
    ) -> Message:
        if isinstance(agent, AgentExecutor):
            runnable = agent
        else:
            # note the tools are not required to run the agent, hence the validation removed.
            handle_parsing_errors = hasattr(self, "handle_parsing_errors") and self.handle_parsing_errors
            verbose = hasattr(self, "verbose") and self.verbose
            max_iterations = hasattr(self, "max_iterations") and self.max_iterations
            runnable = AgentExecutor.from_agent_and_tools(
                agent=agent,
                tools=self.tools or [],
                handle_parsing_errors=handle_parsing_errors,
                verbose=verbose,
                max_iterations=max_iterations,
            )
        # Convert input_value to proper format for agent
        lc_message = None
        if isinstance(self.input_value, Message):
            lc_message = self.input_value.to_lc_message()
            # Extract text content from the LangChain message for agent input
            # Agents expect a string input, not a Message object
            if hasattr(lc_message, "content"):
                if isinstance(lc_message.content, str):
                    input_dict: dict[str, str | list[BaseMessage] | BaseMessage] = {"input": lc_message.content}
                elif isinstance(lc_message.content, list):
                    # For multimodal content, extract text parts
                    text_parts = [item.get("text", "") for item in lc_message.content if item.get("type") == "text"]
                    input_dict = {"input": " ".join(text_parts) if text_parts else ""}
                else:
                    input_dict = {"input": str(lc_message.content)}
            else:
                input_dict = {"input": str(lc_message)}
        else:
            input_dict = {"input": self.input_value}

        # Ensure input_dict is initialized
        if "input" not in input_dict:
            input_dict = {"input": self.input_value}

        # Use enhanced prompt if available (set by IBM Granite handler), otherwise use original
        system_prompt_to_use = getattr(self, "_effective_system_prompt", None) or getattr(self, "system_prompt", None)
        if system_prompt_to_use and system_prompt_to_use.strip():
            input_dict["system_prompt"] = system_prompt_to_use

        if hasattr(self, "chat_history") and self.chat_history:
            if isinstance(self.chat_history, Data):
                input_dict["chat_history"] = self._data_to_messages_skip_empty([self.chat_history])
            elif all(hasattr(m, "to_data") and callable(m.to_data) and "text" in m.data for m in self.chat_history):
                input_dict["chat_history"] = self._data_to_messages_skip_empty(self.chat_history)
            elif all(isinstance(m, Message) for m in self.chat_history):
                input_dict["chat_history"] = self._data_to_messages_skip_empty([m.to_data() for m in self.chat_history])

        # Handle multimodal input (images + text)
        # Note: Agent input must be a string, so we extract text and move images to chat_history
        if lc_message is not None and hasattr(lc_message, "content") and isinstance(lc_message.content, list):
            # Extract images and text from the text content items
            # Support both "image" (legacy) and "image_url" (standard) types
            image_dicts = [item for item in lc_message.content if item.get("type") in ("image", "image_url")]
            text_content = [item for item in lc_message.content if item.get("type") not in ("image", "image_url")]

            text_strings = [
                item.get("text", "")
                for item in text_content
                if item.get("type") == "text" and item.get("text", "").strip()
            ]

            # Set input to concatenated text or empty string
            input_dict["input"] = " ".join(text_strings) if text_strings else ""

            # If input is still a list or empty, provide a default
            if isinstance(input_dict["input"], list) or not input_dict["input"]:
                input_dict["input"] = "Process the provided images."

            if "chat_history" not in input_dict:
                input_dict["chat_history"] = []

            if isinstance(input_dict["chat_history"], list):
                input_dict["chat_history"].extend(HumanMessage(content=[image_dict]) for image_dict in image_dicts)
            else:
                input_dict["chat_history"] = [HumanMessage(content=[image_dict]) for image_dict in image_dicts]

        # Final safety check: ensure input is never empty (prevents Anthropic API errors)
        current_input = input_dict.get("input", "")
        if isinstance(current_input, list):
            current_input = " ".join(map(str, current_input))
        elif not isinstance(current_input, str):
            current_input = str(current_input)

        if not current_input.strip():
            input_dict["input"] = "Continue the conversation."
        else:
            input_dict["input"] = current_input

        if hasattr(self, "graph"):
            session_id = self.graph.session_id
        elif hasattr(self, "_session_id"):
            session_id = self._session_id
        else:
            session_id = None

        sender_name = get_chat_output_sender_name(self) or self.display_name or "AI"
        agent_message = Message(
            sender=MESSAGE_SENDER_AI,
            sender_name=sender_name,
            properties={"icon": "Bot", "state": "partial"},
            content_blocks=[ContentBlock(title="Agent Steps", contents=[])],
            session_id=session_id or uuid.uuid4(),
        )

        # Create token callback if event_manager is available
        # This wraps the event_manager's on_token method to match OnTokenFunctionType Protocol
        on_token_callback: OnTokenFunctionType | None = None
        if self._event_manager:
            on_token_callback = cast("OnTokenFunctionType", self._event_manager.on_token)

        token_usage_handler = TokenUsageCallbackHandler()

        try:
            result = await process_agent_events(
                runnable.astream_events(
                    input_dict,
                    # here we use the shared callbacks because the AgentExecutor uses the tools
                    config={
                        "callbacks": [
                            AgentAsyncHandler(self.log),
                            token_usage_handler,
                            *self._get_shared_callbacks(),
                        ]
                    },
                    version="v2",
                ),
                agent_message,
                cast("SendMessageFunctionType", self.send_message),
                on_token_callback,
            )
        except ExceptionWithMessageError as e:
            # Only delete message from database if it has an ID (was stored)
            if hasattr(e, "agent_message"):
                msg_id = e.agent_message.get_id()
                if msg_id:
                    await delete_message(id_=msg_id)
            await self._send_message_event(e.agent_message, category="remove_message")
            logger.error(f"ExceptionWithMessageError: {e}")
            raise
        except Exception as e:
            # Log or handle any other exceptions
            logger.error(f"Error: {e}")
            raise

        # Extract accumulated token usage from callback handler
        usage_data = token_usage_handler.get_usage()
        if usage_data:
            self._token_usage = usage_data
            result.properties.usage = usage_data
            # Only update DB and send event if the message was stored (has an ID)
            if result.get_id():
                stored_result = await self._update_stored_message(result)
                await self._send_message_event(stored_result)
                result = stored_result

        self.status = result
        return result
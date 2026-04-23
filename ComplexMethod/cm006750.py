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
        runnable = self.update_runnable_instance(agent, runnable, self.tools)

        # Convert input_value to proper format for agent
        if hasattr(self.input_value, "to_lc_message") and callable(self.input_value.to_lc_message):
            lc_message = self.input_value.to_lc_message()
            input_text = lc_message.content if hasattr(lc_message, "content") else str(lc_message)
        else:
            lc_message = None
            input_text = self.input_value

        input_dict: dict[str, str | list[BaseMessage]] = {}
        if hasattr(self, "system_prompt"):
            input_dict["system_prompt"] = self.system_prompt
        if hasattr(self, "chat_history") and self.chat_history:
            if (
                hasattr(self.chat_history, "to_data")
                and callable(self.chat_history.to_data)
                and self.chat_history.__class__.__name__ == "Data"
            ):
                input_dict["chat_history"] = data_to_messages(self.chat_history)
            # Handle both lfx.schema.message.Message and langflow.schema.message.Message types
            if all(hasattr(m, "to_data") and callable(m.to_data) and "text" in m.data for m in self.chat_history):
                input_dict["chat_history"] = data_to_messages(self.chat_history)
            if all(isinstance(m, Message) for m in self.chat_history):
                input_dict["chat_history"] = data_to_messages([m.to_data() for m in self.chat_history])
        if hasattr(lc_message, "content") and isinstance(lc_message.content, list):
            # ! Because the input has to be a string, we must pass the images in the chat_history
            # Support both "image" (legacy) and "image_url" (standard) types
            image_dicts = [item for item in lc_message.content if item.get("type") in ("image", "image_url")]
            lc_message.content = [item for item in lc_message.content if item.get("type") not in ("image", "image_url")]

            if "chat_history" not in input_dict:
                input_dict["chat_history"] = []
            if isinstance(input_dict["chat_history"], list):
                input_dict["chat_history"].extend(HumanMessage(content=[image_dict]) for image_dict in image_dicts)
            else:
                input_dict["chat_history"] = [HumanMessage(content=[image_dict]) for image_dict in image_dicts]
        input_dict["input"] = input_text

        # Copied from agent.py
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

        try:
            sender_name = get_chat_output_sender_name(self)
        except AttributeError:
            sender_name = self.display_name or "AI"

        agent_message = Message(
            sender=MESSAGE_SENDER_AI,
            sender_name=sender_name,
            properties={"icon": "Bot", "state": "partial"},
            content_blocks=[ContentBlock(title="Agent Steps", contents=[])],
            session_id=session_id or uuid.uuid4(),
        )
        try:
            result = await process_agent_events(
                runnable.astream_events(
                    input_dict,
                    config={
                        "callbacks": [
                            AgentAsyncHandler(self.log),
                            *self.get_langchain_callbacks(),
                        ]
                    },
                    version="v2",
                ),
                agent_message,
                cast("SendMessageFunctionType", self.send_message),
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

        self.status = result
        return result
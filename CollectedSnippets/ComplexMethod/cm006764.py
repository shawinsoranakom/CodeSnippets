async def _get_chat_result(
        self,
        *,
        runnable: LanguageModel,
        stream: bool,
        input_value: str | Message,
        system_message: str | None = None,
    ) -> Message:
        """Get chat result from a language model.

        This method handles the core logic of getting a response from a language model,
        including handling different input types, streaming, and error handling.

        Args:
            runnable (LanguageModel): The language model to use for generating responses
            stream (bool): Whether to stream the response
            input_value (str | Message): The input to send to the model
            system_message (str | None, optional): System message to prepend. Defaults to None.

        Returns:
            The model response, either as a Message object or raw content

        Raises:
            ValueError: If the input message is empty or if there's an error during model invocation
        """
        messages: list[BaseMessage] = []
        if not input_value and not system_message:
            msg = "The message you want to send to the model is empty."
            raise ValueError(msg)
        system_message_added = False
        message = None
        if input_value:
            if isinstance(input_value, Message):
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    if "prompt" in input_value:
                        prompt = input_value.load_lc_prompt()
                        if system_message:
                            prompt.messages = [
                                SystemMessage(content=system_message),
                                *prompt.messages,  # type: ignore[has-type]
                            ]
                            system_message_added = True
                        runnable = prompt | runnable
                    else:
                        messages.append(input_value.to_lc_message(self.name))
            else:
                messages.append(HumanMessage(content=input_value))

        if system_message and not system_message_added:
            messages.insert(0, SystemMessage(content=system_message))
        inputs: list | dict = messages or {}
        lf_message = None
        usage_data = None
        try:
            # TODO: Depreciated Feature to be removed in upcoming release
            if hasattr(self, "output_parser") and self.output_parser is not None:
                runnable |= self.output_parser

            runnable = runnable.with_config(
                {
                    "run_name": self.display_name,
                    "project_name": self.get_project_name(),
                    "callbacks": self.get_langchain_callbacks(),
                }
            )
            if stream:
                lf_message, result, message = await self._handle_stream(runnable, inputs)
            else:
                message = await runnable.ainvoke(inputs)
                result = message.content if hasattr(message, "content") else message
            if isinstance(message, AIMessage):
                status_message = self.build_status_message(message)
                self.status = status_message
                # Extract usage for the response
                usage_data = self.extract_usage(message)
                if usage_data:
                    self._token_usage = usage_data
            elif isinstance(result, dict):
                result = json.dumps(message, indent=4)
                self.status = result
            else:
                self.status = result
        except Exception as e:
            if message := self._get_exception_message(e):
                raise ValueError(message) from e
            raise

        if lf_message:
            if lf_message.properties and lf_message.properties.usage:
                self._token_usage = lf_message.properties.usage
            return lf_message

        # Create message with usage data if available
        msg = Message(text=result)
        if usage_data:
            msg.properties.usage = usage_data
        return msg
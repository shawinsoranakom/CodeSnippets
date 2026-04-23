async def ainvoke(
        self,
        input: dict,
        config: RunnableConfig | None = None,
        **kwargs: Any,
    ) -> OutputType:
        """Async invoke assistant.

        Args:
            input: Runnable input dict that can have:
                content: User message when starting a new run.
                thread_id: Existing thread to use.
                run_id: Existing run to use. Should only be supplied when providing
                    the tool output for a required action after an initial invocation.
                message_metadata: Metadata to associate with a new message.
                thread_metadata: Metadata to associate with new thread. Only relevant
                    when a new thread is created.
                instructions: Overrides the instructions of the assistant.
                additional_instructions: Appends additional instructions.
                model: Override Assistant model for this run.
                tools: Override Assistant tools for this run.
                parallel_tool_calls: Allow Assistant to set parallel_tool_calls
                    for this run.
                top_p: Override Assistant top_p for this run.
                temperature: Override Assistant temperature for this run.
                max_completion_tokens: Allow setting max_completion_tokens for this run.
                max_prompt_tokens: Allow setting max_prompt_tokens for this run.
                run_metadata: Metadata to associate with new run.
            config: Runnable config.
            kwargs: Additional arguments.

        Returns:
            If self.as_agent, will return
                Union[List[OpenAIAssistantAction], OpenAIAssistantFinish].
                Otherwise, will return OpenAI types
                Union[List[ThreadMessage], List[RequiredActionFunctionToolCall]].
        """
        config = config or {}
        callback_manager = CallbackManager.configure(
            inheritable_callbacks=config.get("callbacks"),
            inheritable_tags=config.get("tags"),
            inheritable_metadata=config.get("metadata"),
        )
        run_manager = callback_manager.on_chain_start(
            dumpd(self),
            input,
            name=config.get("run_name") or self.get_name(),
        )
        try:
            # Being run within AgentExecutor and there are tool outputs to submit.
            if self.as_agent and input.get("intermediate_steps"):
                tool_outputs = await self._aparse_intermediate_steps(
                    input["intermediate_steps"],
                )
                run = await self.async_client.beta.threads.runs.submit_tool_outputs(
                    **tool_outputs,
                )
            # Starting a new thread and a new run.
            elif "thread_id" not in input:
                thread = {
                    "messages": [
                        {
                            "role": "user",
                            "content": input["content"],
                            "metadata": input.get("message_metadata"),
                        },
                    ],
                    "metadata": input.get("thread_metadata"),
                }
                run = await self._acreate_thread_and_run(input, thread)
            # Starting a new run in an existing thread.
            elif "run_id" not in input:
                _ = await self.async_client.beta.threads.messages.create(
                    input["thread_id"],
                    content=input["content"],
                    role="user",
                    metadata=input.get("message_metadata"),
                )
                run = await self._acreate_run(input)
            # Submitting tool outputs to an existing run, outside the AgentExecutor
            # framework.
            else:
                run = await self.async_client.beta.threads.runs.submit_tool_outputs(
                    **input,
                )
            run = await self._await_for_run(run.id, run.thread_id)
        except BaseException as e:
            run_manager.on_chain_error(e)
            raise
        try:
            # Use async response handler in async ainvoke
            response = await self._aget_response(run)
        except BaseException as e:
            run_manager.on_chain_error(e, metadata=run.dict())
            raise
        else:
            run_manager.on_chain_end(response)
            return response
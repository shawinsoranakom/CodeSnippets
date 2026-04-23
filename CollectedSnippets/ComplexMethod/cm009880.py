def invoke(
        self,
        input: dict,
        config: RunnableConfig | None = None,
        **kwargs: Any,
    ) -> OutputType:
        """Invoke assistant.

        Args:
            input: Runnable input dict that can have:
                content: User message when starting a new run.
                thread_id: Existing thread to use.
                run_id: Existing run to use. Should only be supplied when providing
                    the tool output for a required action after an initial invocation.
                message_metadata: Metadata to associate with new message.
                thread_metadata: Metadata to associate with new thread. Only relevant
                    when new thread being created.
                instructions: Additional run instructions.
                model: Override Assistant model for this run.
                tools: Override Assistant tools for this run.
                parallel_tool_calls: Allow Assistant to set parallel_tool_calls
                    for this run.
                top_p: Override Assistant top_p for this run.
                temperature: Override Assistant temperature for this run.
                max_completion_tokens: Allow setting max_completion_tokens for this run.
                max_prompt_tokens: Allow setting max_prompt_tokens for this run.
                run_metadata: Metadata to associate with new run.
                attachments: A list of files attached to the message, and the
                    tools they should be added to.
            config: Runnable config.
            **kwargs: Additional arguments.

        Returns:
            If self.as_agent, will return
                Union[List[OpenAIAssistantAction], OpenAIAssistantFinish].
                Otherwise, will return OpenAI types
                Union[List[ThreadMessage], List[RequiredActionFunctionToolCall]].
        """
        config = ensure_config(config)
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
                tool_outputs = self._parse_intermediate_steps(
                    input["intermediate_steps"],
                )
                run = self.client.beta.threads.runs.submit_tool_outputs(**tool_outputs)
            # Starting a new thread and a new run.
            elif "thread_id" not in input:
                thread = {
                    "messages": [
                        {
                            "role": "user",
                            "content": input["content"],
                            "metadata": input.get("message_metadata"),
                            "attachments": input.get("attachments"),
                        },
                    ],
                    "metadata": input.get("thread_metadata"),
                }
                run = self._create_thread_and_run(input, thread)
            # Starting a new run in an existing thread.
            elif "run_id" not in input:
                _ = self.client.beta.threads.messages.create(
                    input["thread_id"],
                    content=input["content"],
                    role="user",
                    metadata=input.get("message_metadata"),
                )
                run = self._create_run(input)
            # Submitting tool outputs to an existing run, outside the AgentExecutor
            # framework.
            else:
                run = self.client.beta.threads.runs.submit_tool_outputs(**input)
            run = self._wait_for_run(run.id, run.thread_id)
        except BaseException as e:
            run_manager.on_chain_error(e)
            raise
        try:
            # Use sync response handler in sync invoke
            response = self._get_response(run)
        except BaseException as e:
            run_manager.on_chain_error(e, metadata=run.dict())
            raise
        else:
            run_manager.on_chain_end(response)
            return response
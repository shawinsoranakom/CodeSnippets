async def on_messages_stream(
        self, messages: Sequence[BaseChatMessage], cancellation_token: CancellationToken
    ) -> AsyncGenerator[BaseAgentEvent | BaseChatMessage | Response, None]:
        """
        Process the incoming messages with the assistant agent and yield events/responses as they happen.
        """

        # Gather all relevant state here
        agent_name = self.name
        model_context = self._model_context
        system_messages = self._system_messages
        model_client = self._model_client
        model_client_stream = self._model_client_stream
        max_retries_on_error = self._max_retries_on_error

        execution_result: CodeResult | None = None
        if model_client is None:  # default behaviour for backward compatibility
            # execute generated code if present
            code_blocks: List[CodeBlock] = await self.extract_code_blocks_from_messages(messages)
            if not code_blocks:
                yield Response(
                    chat_message=TextMessage(
                        content=self.NO_CODE_BLOCKS_FOUND_MESSAGE,
                        source=agent_name,
                    )
                )
                return
            execution_result = await self.execute_code_block(code_blocks, cancellation_token)
            yield Response(chat_message=TextMessage(content=execution_result.output, source=self.name))
            return

        inner_messages: List[BaseAgentEvent | BaseChatMessage] = []

        for nth_try in range(max_retries_on_error + 1):  # Do one default generation, execution and inference loop
            # Step 1: Add new user/handoff messages to the model context
            await self._add_messages_to_context(
                model_context=model_context,
                messages=messages,
            )

            # Step 2: Run inference with the model context
            model_result = None
            async for inference_output in self._call_llm(
                model_client=model_client,
                model_client_stream=model_client_stream,
                system_messages=system_messages,
                model_context=model_context,
                agent_name=agent_name,
                cancellation_token=cancellation_token,
            ):
                if isinstance(inference_output, CreateResult):
                    model_result = inference_output
                else:
                    # Streaming chunk event
                    yield inference_output

            assert model_result is not None, "No model result was produced."

            # Step 3: [NEW] If the model produced a hidden "thought," yield it as an event
            if model_result.thought:
                thought_event = ThoughtEvent(content=model_result.thought, source=agent_name)
                yield thought_event
                inner_messages.append(thought_event)

            # Step 4: Add the assistant message to the model context (including thought if present)
            await model_context.add_message(
                AssistantMessage(
                    content=model_result.content,
                    source=agent_name,
                    thought=getattr(model_result, "thought", None),
                )
            )

            # Step 5: Extract the code blocks from inferred text
            assert isinstance(model_result.content, str), "Expected inferred model_result.content to be of type str."
            code_blocks = self._extract_markdown_code_blocks(str(model_result.content))

            # Step 6: Exit the loop if no code blocks found
            if not code_blocks:
                yield Response(
                    chat_message=TextMessage(
                        content=str(model_result.content),
                        source=agent_name,
                    )
                )
                return

            # Step 7: Yield a CodeGenerationEvent
            inferred_text_message: CodeGenerationEvent = CodeGenerationEvent(
                retry_attempt=nth_try,
                content=model_result.content,
                code_blocks=code_blocks,
                source=agent_name,
            )

            yield inferred_text_message

            # Step 8: Execute the extracted code blocks
            execution_result = await self.execute_code_block(inferred_text_message.code_blocks, cancellation_token)

            # Step 9: Update model context with the code execution result
            await model_context.add_message(
                UserMessage(
                    content=execution_result.output,
                    source=agent_name,
                )
            )

            # Step 10: Yield a CodeExecutionEvent
            yield CodeExecutionEvent(retry_attempt=nth_try, result=execution_result, source=self.name)

            # If execution was successful or last retry, then exit
            if execution_result.exit_code == 0 or nth_try == max_retries_on_error:
                break

            # Step 11: If exit code is non-zero and retries are available then
            #          make an inference asking if we should retry or not
            chat_context = await model_context.get_messages()

            retry_prompt = (
                f"The most recent code execution resulted in an error:\n{execution_result.output}\n\n"
                "Should we attempt to resolve it? Please respond with:\n"
                "- A boolean value for 'retry' indicating whether it should be retried.\n"
                "- A detailed explanation in 'reason' that identifies the issue, justifies your decision to retry or not, and outlines how you would resolve the error if a retry is attempted."
            )

            chat_context = chat_context + [
                UserMessage(
                    content=retry_prompt,
                    source=agent_name,
                )
            ]

            response = await model_client.create(messages=chat_context, json_output=RetryDecision)

            assert isinstance(
                response.content, str
            ), "Expected structured response for retry decision to be of type str."
            should_retry_generation = RetryDecision.model_validate_json(str(response.content))

            # Exit if no-retry is needed
            if not should_retry_generation.retry:
                break

            yield CodeGenerationEvent(
                retry_attempt=nth_try,
                content=f"Attempt number: {nth_try + 1}\nProposed correction: {should_retry_generation.reason}",
                code_blocks=[],
                source=agent_name,
            )

        # Always reflect on the execution result
        async for reflection_response in CodeExecutorAgent._reflect_on_code_block_results_flow(
            system_messages=system_messages,
            model_client=model_client,
            model_client_stream=model_client_stream,
            model_context=model_context,
            agent_name=agent_name,
            inner_messages=inner_messages,
        ):
            yield reflection_response
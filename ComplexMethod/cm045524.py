async def handle_user_message(self, message: UserMessage, ctx: MessageContext) -> Message:

        # Append the message to chat history.
        self._chat_history.append(
           message 
        )

        # Add message to model context.
        # await self._model_context.add_message(UserMessage(content=message.content, source="User"))
        model_result: Optional[CreateResult] = None

        async for chunk in self._call_model_client(
            cancellation_token=ctx.cancellation_token,
        ):
            if isinstance(chunk, CreateResult):
                model_result = chunk
            elif isinstance(chunk, str):
                # foward the stream tokent to the Queue
                await self.runtime.publish_message(StreamResult(content=chunk, source=self.id.type), topic_id=task_results_topic_id)
            else:
                raise RuntimeError(f"Invalid chunk type: {type(chunk)}")

        if model_result is None:    # No final result in model client respons
            raise RuntimeError("No final model result in streaming mode.")

        # Add the first model create result to the session.
        self._chat_history.append(AssistantMessage(content=model_result.content, source=self.id.type))

        if isinstance(model_result.content, str):    # No tools, return the result
            await self.runtime.publish_message(StreamResult(content=model_result, source=self.id.type), topic_id=task_results_topic_id)
            return (Message(content= model_result.content))

        # Execute the tool calls.
        assert isinstance(model_result.content, list) and all(
            isinstance(call, FunctionCall) for call in model_result.content
        )
        results = await asyncio.gather(
            *[self._execute_tool_call(call, ctx.cancellation_token) for call in model_result.content]
        )

        # Add the function execution results to the session.
        self._chat_history.append(FunctionExecutionResultMessage(content=results))

        #if (not self._reflect_on_tool_use):
        #    return Message(content=model_result.content)

        # Run the chat completion client again to reflect on the history and function execution results.
        #model_result = None
        model_result2: Optional[CreateResult] = None
        async for chunk in self._call_model_client(
            cancellation_token=ctx.cancellation_token,
        ):
            if isinstance(chunk, CreateResult):
                model_result2 = chunk
            elif isinstance(chunk, str):
                # foward the stream tokent to the Queue
                await self.runtime.publish_message(StreamResult(content=chunk, source=self.id.type), topic_id=task_results_topic_id)
            else:
                raise RuntimeError(f"Invalid chunk type: {type(chunk)}")

        if model_result2 is None:
            raise RuntimeError("No final model result in streaming mode.")
        assert model_result2.content is not None 
        assert isinstance(model_result2.content, str)

        await self.runtime.publish_message(StreamResult(content=model_result2, source=self.id.type), topic_id=task_results_topic_id)

        return Message(content=model_result2.content)
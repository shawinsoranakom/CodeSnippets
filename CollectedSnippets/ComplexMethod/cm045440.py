async def handle_request(self, message: GroupChatRequestPublish, ctx: MessageContext) -> None:
        """Handle a content request event by passing the messages in the buffer
        to the delegate agent and publish the response."""
        if isinstance(self._agent, Team):
            try:
                stream = self._agent.run_stream(
                    task=self._message_buffer,
                    cancellation_token=ctx.cancellation_token,
                    output_task_messages=False,
                )
                result: TaskResult | None = None
                async for team_event in stream:
                    if isinstance(team_event, TaskResult):
                        result = team_event
                    else:
                        await self._log_message(team_event)
                if result is None:
                    raise RuntimeError(
                        "The team did not produce a final TaskResult. Check the team's run_stream method."
                    )
                self._message_buffer.clear()
                # Publish the team response to the group chat.
                await self.publish_message(
                    GroupChatTeamResponse(result=result, name=self._agent.name),
                    topic_id=DefaultTopicId(type=self._parent_topic_type),
                    cancellation_token=ctx.cancellation_token,
                )
            except Exception as e:
                # Publish the error to the group chat.
                error_message = SerializableException.from_exception(e)
                await self.publish_message(
                    GroupChatError(error=error_message),
                    topic_id=DefaultTopicId(type=self._parent_topic_type),
                    cancellation_token=ctx.cancellation_token,
                )
                # Raise the error to the runtime.
                raise
        else:
            # If the agent is not a team, handle it as a single agent.
            with trace_invoke_agent_span(
                agent_name=self._agent.name,
                agent_description=self._agent.description,
                agent_id=str(self.id),
            ):
                try:
                    # Pass the messages in the buffer to the delegate agent.
                    response: Response | None = None
                    async for msg in self._agent.on_messages_stream(self._message_buffer, ctx.cancellation_token):
                        if isinstance(msg, Response):
                            await self._log_message(msg.chat_message)
                            response = msg
                        else:
                            await self._log_message(msg)
                    if response is None:
                        raise RuntimeError(
                            "The agent did not produce a final response. Check the agent's on_messages_stream method."
                        )
                    # Publish the response to the group chat.
                    self._message_buffer.clear()
                    await self.publish_message(
                        GroupChatAgentResponse(response=response, name=self._agent.name),
                        topic_id=DefaultTopicId(type=self._parent_topic_type),
                        cancellation_token=ctx.cancellation_token,
                    )
                except Exception as e:
                    # Publish the error to the group chat.
                    error_message = SerializableException.from_exception(e)
                    await self.publish_message(
                        GroupChatError(error=error_message),
                        topic_id=DefaultTopicId(type=self._parent_topic_type),
                        cancellation_token=ctx.cancellation_token,
                    )
                    # Raise the error to the runtime.
                    raise
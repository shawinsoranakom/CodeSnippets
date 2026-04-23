async def _process_publish(self, message_envelope: PublishMessageEnvelope) -> None:
        with self._tracer_helper.trace_block("publish", message_envelope.topic_id, parent=message_envelope.metadata):
            try:
                responses: List[Awaitable[Any]] = []
                recipients = await self._subscription_manager.get_subscribed_recipients(message_envelope.topic_id)
                for agent_id in recipients:
                    # Avoid sending the message back to the sender
                    if message_envelope.sender is not None and agent_id == message_envelope.sender:
                        continue

                    sender_agent = (
                        await self._get_agent(message_envelope.sender) if message_envelope.sender is not None else None
                    )
                    sender_name = str(sender_agent.id) if sender_agent is not None else "Unknown"
                    logger.info(
                        f"Calling message handler for {agent_id.type} with message type {type(message_envelope.message).__name__} published by {sender_name}"
                    )
                    event_logger.info(
                        MessageEvent(
                            payload=self._try_serialize(message_envelope.message),
                            sender=message_envelope.sender,
                            receiver=None,
                            kind=MessageKind.PUBLISH,
                            delivery_stage=DeliveryStage.DELIVER,
                        )
                    )
                    message_context = MessageContext(
                        sender=message_envelope.sender,
                        topic_id=message_envelope.topic_id,
                        is_rpc=False,
                        cancellation_token=message_envelope.cancellation_token,
                        message_id=message_envelope.message_id,
                    )
                    agent = await self._get_agent(agent_id)

                    async def _on_message(agent: Agent, message_context: MessageContext) -> Any:
                        with self._tracer_helper.trace_block(
                            "process",
                            agent.id,
                            parent=message_envelope.metadata,
                            attributes=await self._create_otel_attributes(
                                sender_agent_id=message_envelope.sender,
                                recipient_agent_id=agent.id,
                                message_context=message_context,
                                message=message_envelope.message,
                            ),
                        ):
                            with MessageHandlerContext.populate_context(agent.id):
                                try:
                                    return await agent.on_message(
                                        message_envelope.message,
                                        ctx=message_context,
                                    )
                                except BaseException as e:
                                    logger.error(f"Error processing publish message for {agent.id}", exc_info=True)
                                    event_logger.info(
                                        MessageHandlerExceptionEvent(
                                            payload=self._try_serialize(message_envelope.message),
                                            handling_agent=agent.id,
                                            exception=e,
                                        )
                                    )
                                    raise e

                    future = _on_message(agent, message_context)
                    responses.append(future)

                await asyncio.gather(*responses)
            except BaseException as e:
                if not self._ignore_unhandled_handler_exceptions:
                    self._background_exception = e
            finally:
                self._message_queue.task_done()
async def _process_next(self) -> None:
        """Process the next message in the queue."""

        if self._background_exception is not None:
            e = self._background_exception
            self._background_exception = None
            self._message_queue.shutdown(immediate=True)  # type: ignore
            raise e

        try:
            message_envelope = await self._message_queue.get()
        except QueueShutDown:
            if self._background_exception is not None:
                e = self._background_exception
                self._background_exception = None
                raise e from None
            return

        match message_envelope:
            case SendMessageEnvelope(message=message, sender=sender, recipient=recipient, future=future):
                if self._intervention_handlers is not None:
                    for handler in self._intervention_handlers:
                        with self._tracer_helper.trace_block(
                            "intercept", handler.__class__.__name__, parent=message_envelope.metadata
                        ):
                            try:
                                message_context = MessageContext(
                                    sender=sender,
                                    topic_id=None,
                                    is_rpc=True,
                                    cancellation_token=message_envelope.cancellation_token,
                                    message_id=message_envelope.message_id,
                                )
                                temp_message = await handler.on_send(
                                    message, message_context=message_context, recipient=recipient
                                )
                                _warn_if_none(temp_message, "on_send")
                            except BaseException as e:
                                future.set_exception(e)
                                return
                            if temp_message is DropMessage or isinstance(temp_message, DropMessage):
                                event_logger.info(
                                    MessageDroppedEvent(
                                        payload=self._try_serialize(message),
                                        sender=sender,
                                        receiver=recipient,
                                        kind=MessageKind.DIRECT,
                                    )
                                )
                                future.set_exception(MessageDroppedException())
                                return

                        message_envelope.message = temp_message
                task = asyncio.create_task(self._process_send(message_envelope))
                self._background_tasks.add(task)
                task.add_done_callback(self._background_tasks.discard)
            case PublishMessageEnvelope(
                message=message,
                sender=sender,
                topic_id=topic_id,
            ):
                if self._intervention_handlers is not None:
                    for handler in self._intervention_handlers:
                        with self._tracer_helper.trace_block(
                            "intercept", handler.__class__.__name__, parent=message_envelope.metadata
                        ):
                            try:
                                message_context = MessageContext(
                                    sender=sender,
                                    topic_id=topic_id,
                                    is_rpc=False,
                                    cancellation_token=message_envelope.cancellation_token,
                                    message_id=message_envelope.message_id,
                                )
                                temp_message = await handler.on_publish(message, message_context=message_context)
                                _warn_if_none(temp_message, "on_publish")
                            except BaseException as e:
                                # TODO: we should raise the intervention exception to the publisher.
                                logger.error(f"Exception raised in in intervention handler: {e}", exc_info=True)
                                return
                            if temp_message is DropMessage or isinstance(temp_message, DropMessage):
                                event_logger.info(
                                    MessageDroppedEvent(
                                        payload=self._try_serialize(message),
                                        sender=sender,
                                        receiver=topic_id,
                                        kind=MessageKind.PUBLISH,
                                    )
                                )
                                return

                        message_envelope.message = temp_message

                task = asyncio.create_task(self._process_publish(message_envelope))
                self._background_tasks.add(task)
                task.add_done_callback(self._background_tasks.discard)
            case ResponseMessageEnvelope(message=message, sender=sender, recipient=recipient, future=future):
                if self._intervention_handlers is not None:
                    for handler in self._intervention_handlers:
                        try:
                            temp_message = await handler.on_response(message, sender=sender, recipient=recipient)
                            _warn_if_none(temp_message, "on_response")
                        except BaseException as e:
                            # TODO: should we raise the exception to sender of the response instead?
                            future.set_exception(e)
                            return
                        if temp_message is DropMessage or isinstance(temp_message, DropMessage):
                            event_logger.info(
                                MessageDroppedEvent(
                                    payload=self._try_serialize(message),
                                    sender=sender,
                                    receiver=recipient,
                                    kind=MessageKind.RESPOND,
                                )
                            )
                            future.set_exception(MessageDroppedException())
                            return
                        message_envelope.message = temp_message
                task = asyncio.create_task(self._process_response(message_envelope))
                self._background_tasks.add(task)
                task.add_done_callback(self._background_tasks.discard)

        # Yield control to the message loop to allow other tasks to run
        await asyncio.sleep(0)
async def _process_event(self, event: cloudevent_pb2.CloudEvent) -> None:
        event_attributes = event.attributes
        sender: AgentId | None = None
        if (
            _constants.AGENT_SENDER_TYPE_ATTR in event_attributes
            and _constants.AGENT_SENDER_KEY_ATTR in event_attributes
        ):
            sender = AgentId(
                event_attributes[_constants.AGENT_SENDER_TYPE_ATTR].ce_string,
                event_attributes[_constants.AGENT_SENDER_KEY_ATTR].ce_string,
            )
        topic_id = TopicId(event.type, event.source)
        # Get the recipients for the topic.
        recipients = await self._subscription_manager.get_subscribed_recipients(topic_id)

        message_content_type = event_attributes[_constants.DATA_CONTENT_TYPE_ATTR].ce_string
        message_type = event_attributes[_constants.DATA_SCHEMA_ATTR].ce_string

        if message_content_type == JSON_DATA_CONTENT_TYPE:
            message = self._serialization_registry.deserialize(
                event.binary_data, type_name=message_type, data_content_type=message_content_type
            )
        elif message_content_type == PROTOBUF_DATA_CONTENT_TYPE:
            # TODO: find a way to prevent the roundtrip serialization
            proto_binary_data = event.proto_data.SerializeToString()
            message = self._serialization_registry.deserialize(
                proto_binary_data, type_name=message_type, data_content_type=message_content_type
            )
        else:
            raise ValueError(f"Unsupported message content type: {message_content_type}")

        # TODO: dont read these values in the runtime
        topic_type_suffix = topic_id.type.split(":", maxsplit=1)[1] if ":" in topic_id.type else ""
        is_rpc = topic_type_suffix == _constants.MESSAGE_KIND_VALUE_RPC_REQUEST
        is_marked_rpc_type = (
            _constants.MESSAGE_KIND_ATTR in event_attributes
            and event_attributes[_constants.MESSAGE_KIND_ATTR].ce_string == _constants.MESSAGE_KIND_VALUE_RPC_REQUEST
        )
        if is_rpc and not is_marked_rpc_type:
            warnings.warn("Received RPC request with topic type suffix but not marked as RPC request.", stacklevel=2)

        # Send the message to each recipient.
        responses: List[Awaitable[Any]] = []
        for agent_id in recipients:
            if agent_id == sender:
                continue
            message_context = MessageContext(
                sender=sender,
                topic_id=topic_id,
                is_rpc=is_rpc,
                cancellation_token=CancellationToken(),
                message_id=event.id,
            )
            agent = await self._get_agent(agent_id)
            with MessageHandlerContext.populate_context(agent.id):

                def stringify_attributes(
                    attributes: Mapping[str, cloudevent_pb2.CloudEvent.CloudEventAttributeValue],
                ) -> Mapping[str, str]:
                    result: Dict[str, str] = {}
                    for key, value in attributes.items():
                        item = None
                        match value.WhichOneof("attr"):
                            case "ce_boolean":
                                item = str(value.ce_boolean)
                            case "ce_integer":
                                item = str(value.ce_integer)
                            case "ce_string":
                                item = value.ce_string
                            case "ce_bytes":
                                item = str(value.ce_bytes)
                            case "ce_uri":
                                item = value.ce_uri
                            case "ce_uri_ref":
                                item = value.ce_uri_ref
                            case "ce_timestamp":
                                item = str(value.ce_timestamp)
                            case _:
                                raise ValueError("Unknown attribute kind")
                        result[key] = item

                    return result

                async def send_message(agent: Agent, message_context: MessageContext) -> Any:
                    with self._trace_helper.trace_block(
                        "process",
                        agent.id,
                        parent=stringify_attributes(event.attributes),
                        extraAttributes={"message_type": message_type},
                    ):
                        await agent.on_message(message, ctx=message_context)

                future = send_message(agent, message_context)
            responses.append(future)
        # Wait for all responses.
        try:
            await asyncio.gather(*responses)
        except BaseException as e:
            logger.error("Error handling event", exc_info=e)
async def _create_otel_attributes(
        self,
        sender_agent_id: AgentId | None = None,
        recipient_agent_id: AgentId | None = None,
        message_context: MessageContext | None = None,
        message: Any = None,
    ) -> Mapping[str, str]:
        """Create OpenTelemetry attributes for the given agent and message.

        Args:
            sender_agent (Agent, optional): The sender agent instance.
            recipient_agent (Agent, optional): The recipient agent instance.
            message (Any): The message instance.

        Returns:
            Attributes: A dictionary of OpenTelemetry attributes.
        """
        if not sender_agent_id and not recipient_agent_id and not message:
            return {}
        attributes: Dict[str, str] = {}
        if sender_agent_id:
            sender_agent = await self._get_agent(sender_agent_id)
            attributes["sender_agent_type"] = sender_agent.id.type
            attributes["sender_agent_class"] = sender_agent.__class__.__name__
        if recipient_agent_id:
            recipient_agent = await self._get_agent(recipient_agent_id)
            attributes["recipient_agent_type"] = recipient_agent.id.type
            attributes["recipient_agent_class"] = recipient_agent.__class__.__name__

        if message_context:
            serialized_message_context = {
                "sender": str(message_context.sender),
                "topic_id": str(message_context.topic_id),
                "is_rpc": message_context.is_rpc,
                "message_id": message_context.message_id,
            }
            attributes["message_context"] = json.dumps(serialized_message_context)

        if message:
            try:
                serialized_message = self._try_serialize(message)
            except Exception as e:
                serialized_message = str(e)
        else:
            serialized_message = "No Message"
        attributes["message"] = serialized_message

        return attributes
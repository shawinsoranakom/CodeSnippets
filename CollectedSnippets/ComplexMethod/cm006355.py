def from_message(cls, message: "Message", flow_id: str | UUID | None = None):
        if message.text is None or not message.sender or not message.sender_name:
            msg = "The message does not have the required fields (text, sender, sender_name)."
            raise ValueError(msg)

        if message.files:
            image_paths = []
            for file in message.files:
                if hasattr(file, "path") and hasattr(file, "url") and file.path:
                    session_id = message.session_id
                    if session_id and str(session_id) in file.path:
                        parts = file.path.split(str(session_id))
                        if len(parts) > 1:
                            image_paths.append(f"{session_id}{parts[1]}")
                        else:
                            image_paths.append(file.path)
                    else:
                        image_paths.append(file.path)
                elif isinstance(file, str):
                    image_paths.append(file)

            if image_paths:
                message.files = image_paths

        if isinstance(message.timestamp, str):
            try:
                timestamp = datetime.strptime(message.timestamp, "%Y-%m-%d %H:%M:%S %Z").replace(tzinfo=timezone.utc)
            except ValueError:
                timestamp = datetime.fromisoformat(message.timestamp).replace(tzinfo=timezone.utc)
        else:
            timestamp = message.timestamp

        if not flow_id and message.flow_id:
            flow_id = message.flow_id

        message_text = "" if not isinstance(message.text, str) else message.text

        properties = (
            message.properties.model_dump_json()
            if hasattr(message.properties, "model_dump_json")
            else message.properties
        )

        content_blocks = []
        for content_block in message.content_blocks or []:
            content = content_block.model_dump_json() if hasattr(content_block, "model_dump_json") else content_block
            content_blocks.append(content)

        if isinstance(flow_id, str):
            try:
                flow_id = UUID(flow_id)
            except ValueError as exc:
                msg = f"Flow ID {flow_id} is not a valid UUID"
                raise ValueError(msg) from exc

        return cls(
            sender=message.sender,
            sender_name=message.sender_name,
            text=message_text,
            session_id=message.session_id,
            context_id=message.context_id,
            files=message.files or [],
            timestamp=timestamp,
            flow_id=flow_id,
            properties=properties,
            category=message.category,
            content_blocks=content_blocks,
            session_metadata=getattr(message, "session_metadata", None),
        )
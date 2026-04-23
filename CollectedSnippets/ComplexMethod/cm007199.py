def extract_messages_from_artifacts(self, artifacts: dict[str, Any]) -> list[dict]:
        """Extracts messages from the artifacts.

        Args:
            artifacts (Dict[str, Any]): The artifacts to extract messages from.

        Returns:
            List[str]: The extracted messages.
        """
        messages = []
        for key, artifact in artifacts.items():
            if any(
                k not in artifact for k in ["text", "sender", "sender_name", "session_id", "stream_url"]
            ) and not isinstance(artifact, Message):
                continue
            message_dict = artifact if isinstance(artifact, dict) else artifact.model_dump()
            if not message_dict.get("text"):
                continue
            with contextlib.suppress(KeyError):
                messages.append(
                    ChatOutputResponse(
                        message=message_dict["text"],
                        sender=message_dict.get("sender"),
                        sender_name=message_dict.get("sender_name"),
                        session_id=message_dict.get("session_id"),
                        stream_url=message_dict.get("stream_url"),
                        files=[
                            {"path": file} if isinstance(file, str) else file for file in message_dict.get("files", [])
                        ],
                        component_id=self.id,
                        type=self.artifacts_type[key],
                    ).model_dump(exclude_none=True)
                )
        return messages
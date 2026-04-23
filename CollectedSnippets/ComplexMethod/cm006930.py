async def _send_message_event(self, message: Message, id_: str | None = None, category: str | None = None) -> None:
        if hasattr(self, "_event_manager") and self._event_manager:
            # Use full model_dump() to include all Message fields (content_blocks, properties, etc.)
            data_dict = message.model_dump()

            # The message ID is stored in message.data["id"], which ends up in data_dict["data"]["id"]
            # But the frontend expects it at data_dict["id"], so we need to copy it to the top level
            message_id = id_ or data_dict.get("data", {}).get("id") or getattr(message, "id", None)
            if message_id and not data_dict.get("id"):
                data_dict["id"] = message_id

            category = category or data_dict.get("category", None)

            def _send_event():
                match category:
                    case "error":
                        self._event_manager.on_error(data=data_dict)
                    case "remove_message":
                        # Check if id exists in data_dict before accessing it
                        if "id" in data_dict:
                            self._event_manager.on_remove_message(data={"id": data_dict["id"]})
                        else:
                            # If no id, try to get it from the message object or id_ parameter
                            message_id = getattr(message, "id", None) or id_
                            if message_id:
                                self._event_manager.on_remove_message(data={"id": message_id})
                    case _:
                        self._event_manager.on_message(data=data_dict)

            await asyncio.to_thread(_send_event)
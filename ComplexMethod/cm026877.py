async def _send_message(
        self, message: str, target_rooms: list[RoomAnyID], data: dict | None
    ) -> None:
        """Send a message to the Matrix server."""
        content: dict[str, Any] = {"msgtype": "m.text", "body": message}
        if data is not None:
            thread_id: str | None = data.get(ATTR_THREAD_ID)
            if data.get(ATTR_FORMAT) == FORMAT_HTML:
                content |= {
                    "format": "org.matrix.custom.html",
                    "formatted_body": message,
                }
            if thread_id is not None:
                content["m.relates_to"] = {
                    "event_id": thread_id,
                    "rel_type": "m.thread",
                }

        await self._handle_multi_room_send(
            target_rooms=target_rooms, message_type="m.room.message", content=content
        )

        if (
            data is not None
            and (image_paths := data.get(ATTR_IMAGES, []))
            and len(target_rooms) > 0
        ):
            image_tasks = [
                self.hass.async_create_task(
                    self._send_image(
                        image_path, target_rooms, data.get(ATTR_THREAD_ID)
                    ),
                    eager_start=False,
                )
                for image_path in image_paths
            ]
            await asyncio.wait(image_tasks)
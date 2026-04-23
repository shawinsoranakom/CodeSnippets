async def _handle_room_message(self, room: MatrixRoom, message: Event) -> None:
        """Handle a message sent to a Matrix room."""
        # Corresponds to message type 'm.text' and NOT other RoomMessage subtypes, like 'm.notice' and 'm.emote'.
        if not isinstance(message, (RoomMessageText, ReactionEvent)):
            return
        # Don't respond to our own messages.
        if message.sender == self._mx_id:
            return

        room_id = RoomID(room.room_id)

        if isinstance(message, ReactionEvent):
            # Handle reactions
            reaction = message.key
            _LOGGER.debug("Handling reaction: %s", reaction)
            if command := self._reaction_commands.get(room_id, {}).get(reaction):
                message_data = {
                    "command": command[CONF_NAME],
                    "sender": message.sender,
                    "room": room_id,
                    "event_id": message.reacts_to,
                    "args": {
                        "reaction": message.key,
                    },
                }
                self.hass.bus.async_fire(EVENT_MATRIX_COMMAND, message_data)
            return

        _LOGGER.debug("Handling message: %s", message.body)

        if message.body.startswith("!"):
            # Could trigger a single-word command.
            pieces = message.body.split()
            word = WordCommand(pieces[0].lstrip("!"))

            if command := self._word_commands.get(room_id, {}).get(word):
                message_data = {
                    "command": command[CONF_NAME],
                    "sender": message.sender,
                    "room": room_id,
                    "event_id": message.event_id,
                    "args": pieces[1:],
                    "thread_parent": self._get_thread_parent(message)
                    or message.event_id,
                }

                self.hass.bus.async_fire(EVENT_MATRIX_COMMAND, message_data)

        # After single-word commands, check all regex commands in the room.
        for command in self._expression_commands.get(room_id, []):
            match = command[CONF_EXPRESSION].match(message.body)
            if not match:
                continue
            message_data = {
                "command": command[CONF_NAME],
                "sender": message.sender,
                "room": room_id,
                "event_id": message.event_id,
                "args": match.groupdict(),
                "thread_parent": self._get_thread_parent(message) or message.event_id,
            }

            self.hass.bus.async_fire(EVENT_MATRIX_COMMAND, message_data)
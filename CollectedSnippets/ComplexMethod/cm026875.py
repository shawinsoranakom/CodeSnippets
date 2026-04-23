def _load_commands(self, commands: list[ConfigCommand]) -> None:
        for command in commands:
            # Set the command for all listening_rooms, unless otherwise specified.
            if rooms := command.get(CONF_ROOMS):
                command[CONF_ROOMS] = [self._listening_rooms[room] for room in rooms]
            else:
                command[CONF_ROOMS] = list(self._listening_rooms.values())

            # COMMAND_SCHEMA guarantees that exactly one of CONF_WORD, CONF_EXPRESSION, or CONF_REACTION are set.
            if (word_command := command.get(CONF_WORD)) is not None:
                for room_id in command[CONF_ROOMS]:
                    self._word_commands.setdefault(room_id, {})
                    self._word_commands[room_id][word_command] = command
            elif (reaction_command := command.get(CONF_REACTION)) is not None:
                for room_id in command[CONF_ROOMS]:
                    self._reaction_commands.setdefault(room_id, {})
                    self._reaction_commands[room_id][reaction_command] = command
            else:
                for room_id in command[CONF_ROOMS]:
                    self._expression_commands.setdefault(room_id, [])
                    self._expression_commands[room_id].append(command)
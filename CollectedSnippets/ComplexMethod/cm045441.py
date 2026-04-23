async def validate_group_state(self, messages: List[BaseChatMessage] | None) -> None:
        """Validate the start messages for the group chat."""
        # Check if any of the start messages is a handoff message.
        if messages:
            for message in messages:
                if isinstance(message, HandoffMessage):
                    if message.target not in self._participant_names:
                        raise ValueError(
                            f"The target {message.target} is not one of the participants {self._participant_names}. "
                            "If you are resuming Swarm with a new HandoffMessage make sure to set the target to a valid participant as the target."
                        )
                    return

        # Check if there is a handoff message in the thread that is not targeting a valid participant.
        for existing_message in reversed(self._message_thread):
            if isinstance(existing_message, HandoffMessage):
                if existing_message.target not in self._participant_names:
                    raise ValueError(
                        f"The existing handoff target {existing_message.target} is not one of the participants {self._participant_names}. "
                        "If you are resuming Swarm with a new task make sure to include in your task "
                        "a HandoffMessage with a valid participant as the target. For example, if you are "
                        "resuming from a HandoffTermination, make sure the new task is a HandoffMessage "
                        "with a valid participant as the target."
                    )
                # The latest handoff message should always target a valid participant.
                # Do not look past the latest handoff message.
                return
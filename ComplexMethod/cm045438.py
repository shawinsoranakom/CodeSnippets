async def select_speaker(self, thread: Sequence[BaseAgentEvent | BaseChatMessage]) -> List[str] | str:
        """Selects the next speaker in a group chat using a ChatCompletion client,
        with the selector function as override if it returns a speaker name.

        .. note::

            This method always returns a single speaker name.

        A key assumption is that the agent type is the same as the topic type, which we use as the agent name.
        """
        # Use the selector function if provided.
        if self._selector_func is not None:
            if self._is_selector_func_async:
                async_selector_func = cast(AsyncSelectorFunc, self._selector_func)
                speaker = await async_selector_func(thread)
            else:
                sync_selector_func = cast(SyncSelectorFunc, self._selector_func)
                speaker = sync_selector_func(thread)
            if speaker is not None:
                if speaker not in self._participant_names:
                    raise ValueError(
                        f"Selector function returned an invalid speaker name: {speaker}. "
                        f"Expected one of: {self._participant_names}."
                    )
                # Skip the model based selection.
                return [speaker]

        # Use the candidate function to filter participants if provided
        if self._candidate_func is not None:
            if self._is_candidate_func_async:
                async_candidate_func = cast(AsyncCandidateFunc, self._candidate_func)
                participants = await async_candidate_func(thread)
            else:
                sync_candidate_func = cast(SyncCandidateFunc, self._candidate_func)
                participants = sync_candidate_func(thread)
            if not participants:
                raise ValueError("Candidate function must return a non-empty list of participant names.")
            if not all(p in self._participant_names for p in participants):
                raise ValueError(
                    f"Candidate function returned invalid participant names: {participants}. "
                    f"Expected one of: {self._participant_names}."
                )
        else:
            # Construct the candidate agent list to be selected from, skip the previous speaker if not allowed.
            if self._previous_speaker is not None and not self._allow_repeated_speaker:
                participants = [p for p in self._participant_names if p != self._previous_speaker]
            else:
                participants = list(self._participant_names)

        assert len(participants) > 0

        # Construct agent roles.
        # Each agent sould appear on a single line.
        roles = ""
        for topic_type, description in zip(self._participant_names, self._participant_descriptions, strict=True):
            roles += re.sub(r"\s+", " ", f"{topic_type}: {description}").strip() + "\n"
        roles = roles.strip()

        # Select the next speaker.
        if len(participants) > 1:
            agent_name = await self._select_speaker(roles, participants, self._max_selector_attempts)
        else:
            agent_name = participants[0]
        self._previous_speaker = agent_name
        trace_logger.debug(f"Selected speaker: {agent_name}")
        return [agent_name]
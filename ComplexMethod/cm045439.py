async def _select_speaker(self, roles: str, participants: List[str], max_attempts: int) -> str:
        model_context_messages = await self._model_context.get_messages()
        model_context_history = self.construct_message_history(model_context_messages)

        select_speaker_prompt = self._selector_prompt.format(
            roles=roles, participants=str(participants), history=model_context_history
        )

        select_speaker_messages: List[SystemMessage | UserMessage | AssistantMessage]
        if ModelFamily.is_openai(self._model_client.model_info["family"]):
            select_speaker_messages = [SystemMessage(content=select_speaker_prompt)]
        else:
            # Many other models need a UserMessage to respond to
            select_speaker_messages = [UserMessage(content=select_speaker_prompt, source="user")]

        num_attempts = 0
        while num_attempts < max_attempts:
            num_attempts += 1
            if self._model_client_streaming:
                chunk: CreateResult | str = ""
                async for _chunk in self._model_client.create_stream(messages=select_speaker_messages):
                    chunk = _chunk
                    if self._emit_team_events:
                        if isinstance(chunk, str):
                            await self._output_message_queue.put(
                                ModelClientStreamingChunkEvent(content=cast(str, _chunk), source=self._name)
                            )
                        else:
                            assert isinstance(chunk, CreateResult)
                            assert isinstance(chunk.content, str)
                            await self._output_message_queue.put(
                                SelectorEvent(content=chunk.content, source=self._name)
                            )
                # The last chunk must be CreateResult.
                assert isinstance(chunk, CreateResult)
                response = chunk
            else:
                response = await self._model_client.create(messages=select_speaker_messages)
            assert isinstance(response.content, str)
            select_speaker_messages.append(AssistantMessage(content=response.content, source="selector"))
            # NOTE: we use all participant names to check for mentions, even if the previous speaker is not allowed.
            # This is because the model may still select the previous speaker, and we want to catch that.
            mentions = self._mentioned_agents(response.content, self._participant_names)
            if len(mentions) == 0:
                trace_logger.debug(f"Model failed to select a valid name: {response.content} (attempt {num_attempts})")
                feedback = f"No valid name was mentioned. Please select from: {str(participants)}."
                select_speaker_messages.append(UserMessage(content=feedback, source="user"))
            elif len(mentions) > 1:
                trace_logger.debug(f"Model selected multiple names: {str(mentions)} (attempt {num_attempts})")
                feedback = (
                    f"Expected exactly one name to be mentioned. Please select only one from: {str(participants)}."
                )
                select_speaker_messages.append(UserMessage(content=feedback, source="user"))
            else:
                agent_name = list(mentions.keys())[0]
                if (
                    not self._allow_repeated_speaker
                    and self._previous_speaker is not None
                    and agent_name == self._previous_speaker
                ):
                    trace_logger.debug(f"Model selected the previous speaker: {agent_name} (attempt {num_attempts})")
                    feedback = (
                        f"Repeated speaker is not allowed, please select a different name from: {str(participants)}."
                    )
                    select_speaker_messages.append(UserMessage(content=feedback, source="user"))
                else:
                    # Valid selection
                    trace_logger.debug(f"Model selected a valid name: {agent_name} (attempt {num_attempts})")
                    return agent_name

        if self._previous_speaker is not None:
            trace_logger.warning(f"Model failed to select a speaker after {max_attempts}, using the previous speaker.")
            return self._previous_speaker
        trace_logger.warning(
            f"Model failed to select a speaker after {max_attempts} and there was no previous speaker, using the first participant."
        )
        return participants[0]
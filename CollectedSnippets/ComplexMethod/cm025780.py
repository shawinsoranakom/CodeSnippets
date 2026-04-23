def _internal_on_pipeline_event(self, event: PipelineEvent) -> None:
        """Set state based on pipeline stage."""
        if event.type is PipelineEventType.WAKE_WORD_START:
            # Only return to idle if we're not currently responding.
            # The state will return to idle in tts_response_finished.
            if self.state != AssistSatelliteState.RESPONDING:
                self._set_state(AssistSatelliteState.IDLE)
        elif event.type is PipelineEventType.STT_START:
            self._set_state(AssistSatelliteState.LISTENING)
        elif event.type is PipelineEventType.STT_END:
            # Intercepting text for ask question
            if (
                (self._ask_question_future is not None)
                and (not self._ask_question_future.done())
                and event.data
            ):
                self._ask_question_future.set_result(
                    event.data.get("stt_output", {}).get("text")
                )
        elif event.type is PipelineEventType.INTENT_START:
            self._set_state(AssistSatelliteState.PROCESSING)
        elif event.type is PipelineEventType.TTS_START:
            # Wait until tts_response_finished is called to return to waiting state
            self._run_has_tts = True
            self._set_state(AssistSatelliteState.RESPONDING)
        elif event.type is PipelineEventType.RUN_END:
            if not self._run_has_tts:
                self._set_state(AssistSatelliteState.IDLE)

            if (self._ask_question_future is not None) and (
                not self._ask_question_future.done()
            ):
                # No text for ask question
                self._ask_question_future.set_result(None)

        self.on_pipeline_event(event)
async def _run_pipeline_loop(self) -> None:
        """Run a pipeline one or more times."""
        assert self._client is not None
        client_info: Info | None = None
        wake_word_phrase: str | None = None
        run_pipeline: RunPipeline | None = None
        send_ping = True
        self._run_loop_id = ulid_now()

        # Read events and check for pipeline end in parallel
        pipeline_ended_task = self.config_entry.async_create_background_task(
            self.hass, self._pipeline_ended_event.wait(), "satellite pipeline ended"
        )
        client_event_task = self.config_entry.async_create_background_task(
            self.hass, self._client.read_event(), "satellite event read"
        )
        pending = {pipeline_ended_task, client_event_task}

        # Update info from satellite
        await self._client.write_event(Describe().event())

        while self.is_running and (not self.device.is_muted):
            if send_ping:
                # Ensure satellite is still connected
                send_ping = False
                self.config_entry.async_create_background_task(
                    self.hass, self._send_delayed_ping(), "ping satellite"
                )

            async with asyncio.timeout(_PING_TIMEOUT):
                done, pending = await asyncio.wait(
                    pending, return_when=asyncio.FIRST_COMPLETED
                )

                if pipeline_ended_task in done:
                    # Pipeline run end event was received
                    _LOGGER.debug("Pipeline finished")
                    self._pipeline_ended_event.clear()
                    pipeline_ended_task = (
                        self.config_entry.async_create_background_task(
                            self.hass,
                            self._pipeline_ended_event.wait(),
                            "satellite pipeline ended",
                        )
                    )
                    pending.add(pipeline_ended_task)

                    # Clear last wake word detection
                    wake_word_phrase = None

                    if (run_pipeline is not None) and run_pipeline.restart_on_end:
                        # Automatically restart pipeline.
                        # Used with "always on" streaming satellites.
                        self._run_pipeline_once(run_pipeline)
                        continue

                if client_event_task not in done:
                    continue

                client_event = client_event_task.result()
                if client_event is None:
                    raise ConnectionResetError("Satellite disconnected")

                if Pong.is_type(client_event.type):
                    # Satellite is still there, send next ping
                    send_ping = True
                elif Ping.is_type(client_event.type):
                    # Respond to ping from satellite
                    ping = Ping.from_event(client_event)
                    await self._client.write_event(Pong(text=ping.text).event())
                elif RunPipeline.is_type(client_event.type):
                    # Satellite requested pipeline run
                    run_pipeline = RunPipeline.from_event(client_event)
                    self._run_pipeline_once(run_pipeline, wake_word_phrase)
                elif (
                    AudioChunk.is_type(client_event.type) and self._is_pipeline_running
                ):
                    # Microphone audio
                    chunk = AudioChunk.from_event(client_event)
                    chunk = self._chunk_converter.convert(chunk)
                    self._audio_queue.put_nowait(chunk.audio)
                elif AudioStop.is_type(client_event.type) and self._is_pipeline_running:
                    # Stop pipeline
                    _LOGGER.debug("Client requested pipeline to stop")
                    self._audio_queue.put_nowait(None)
                elif Info.is_type(client_event.type):
                    client_info = Info.from_event(client_event)
                    _LOGGER.debug("Updated client info: %s", client_info)
                elif Detection.is_type(client_event.type):
                    detection = Detection.from_event(client_event)
                    wake_word_phrase = detection.name

                    # Resolve wake word name/id to phrase if info is available.
                    #
                    # This allows us to deconflict multiple satellite wake-ups
                    # with the same wake word.
                    if (client_info is not None) and (client_info.wake is not None):
                        found_phrase = False
                        for wake_service in client_info.wake:
                            for wake_model in wake_service.models:
                                if wake_model.name == detection.name:
                                    wake_word_phrase = (
                                        wake_model.phrase or wake_model.name
                                    )
                                    found_phrase = True
                                    break

                            if found_phrase:
                                break

                    _LOGGER.debug("Client detected wake word: %s", wake_word_phrase)
                elif Played.is_type(client_event.type):
                    # TTS response has finished playing on satellite
                    self.tts_response_finished()

                    if self._played_event_received is not None:
                        self._played_event_received.set()
                else:
                    _LOGGER.debug("Unexpected event from satellite: %s", client_event)

                # Next event
                client_event_task = self.config_entry.async_create_background_task(
                    self.hass, self._client.read_event(), "satellite event read"
                )
                pending.add(client_event_task)
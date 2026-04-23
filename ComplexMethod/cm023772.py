async def write_event(self, event: Event):
        """Send."""
        if RunSatellite.is_type(event.type):
            self.run_satellite_event.set()
        elif Detect.is_type(event.type):
            self.detect_event.set()
        elif Detection.is_type(event.type):
            self.detection = Detection.from_event(event)
            self.detection_event.set()
        elif Transcribe.is_type(event.type):
            self.transcribe = Transcribe.from_event(event)
            self.transcribe_event.set()
        elif VoiceStarted.is_type(event.type):
            self.voice_started = VoiceStarted.from_event(event)
            self.voice_started_event.set()
        elif VoiceStopped.is_type(event.type):
            self.voice_stopped = VoiceStopped.from_event(event)
            self.voice_stopped_event.set()
        elif Transcript.is_type(event.type):
            self.transcript = Transcript.from_event(event)
            self.transcript_event.set()
        elif Synthesize.is_type(event.type):
            self.synthesize = Synthesize.from_event(event)
            self.synthesize_event.set()
        elif AudioStart.is_type(event.type):
            self.tts_audio_start_event.set()
        elif AudioChunk.is_type(event.type):
            self.tts_audio_chunk = AudioChunk.from_event(event)
            self.tts_audio_chunks.append(self.tts_audio_chunk)
            self.tts_audio_chunk_event.set()
        elif AudioStop.is_type(event.type):
            self.tts_audio_stop_event.set()
        elif Error.is_type(event.type):
            self.error = Error.from_event(event)
            self.error_event.set()
        elif Pong.is_type(event.type):
            self.pong = Pong.from_event(event)
            self.pong_event.set()
        elif Ping.is_type(event.type):
            self.ping = Ping.from_event(event)
            self.ping_event.set()
        elif TimerStarted.is_type(event.type):
            self.timer_started = TimerStarted.from_event(event)
            self.timer_started_event.set()
        elif TimerUpdated.is_type(event.type):
            self.timer_updated = TimerUpdated.from_event(event)
            self.timer_updated_event.set()
        elif TimerCancelled.is_type(event.type):
            self.timer_cancelled = TimerCancelled.from_event(event)
            self.timer_cancelled_event.set()
        elif TimerFinished.is_type(event.type):
            self.timer_finished = TimerFinished.from_event(event)
            self.timer_finished_event.set()
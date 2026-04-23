async def _process_audio_output(self, result):
        """Process outgoing audio to the speakers."""
        print("🔊 Ready to play audio responses...")

        audio_chunks_count = 0

        async for event in result.stream():
            if self._stop_event.is_set():
                break

            if event.type == "voice_stream_event_audio":
                if self.audio_player:
                    self.audio_player.add_audio(event.data)
                    audio_chunks_count += 1

                    # Progress indicator for long responses
                    if audio_chunks_count % 20 == 0:
                        print(f"🎵 Playing response... ({audio_chunks_count} chunks)")

            elif event.type == "voice_stream_event_lifecycle":
                if event.event == "turn_started":
                    print("🔄 AI is processing your speech...")
                elif event.event == "turn_ended":
                    print("✅ AI response complete. You can speak again.")
                    # Add a small silence buffer between turns
                    if self.audio_player:
                        self.audio_player.add_audio(create_silence(0.5))

            elif event.type == "voice_stream_event_error":
                print(f"❌ Voice error: {event.error}")

        print("⏹️ Audio output processing stopped")
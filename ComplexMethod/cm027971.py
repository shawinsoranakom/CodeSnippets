async def main():
    """Main function to run the static voice agent example."""
    print("🎙️ Static Voice Agent Demo")
    print("=" * 50)
    print()

    # Create the voice pipeline with our agent and callbacks
    pipeline = VoicePipeline(
        workflow=SingleAgentVoiceWorkflow(agent, callbacks=WorkflowCallbacks())
    )

    print("This demo will:")
    print("1. 🎤 Record your voice for a few seconds")
    print("2. 🔄 Transcribe your speech to text")
    print("3. 🤖 Process with AI agent")
    print("4. 🔊 Convert response back to speech")
    print()

    # Record audio input
    try:
        audio_buffer = record_audio(duration=5.0)
        print(f"📊 Recorded {len(audio_buffer)} audio samples")

        # Create audio input for the pipeline
        audio_input = AudioInput(buffer=audio_buffer)

        # Run the voice pipeline
        print("\n🔄 Processing with voice pipeline...")
        result = await pipeline.run(audio_input)

        # Play the result audio
        print("🔊 Playing AI response...")

        with AudioPlayer() as player:
            audio_chunks_received = 0
            lifecycle_events = 0

            async for event in result.stream():
                if event.type == "voice_stream_event_audio":
                    player.add_audio(event.data)
                    audio_chunks_received += 1
                    if audio_chunks_received % 10 == 0:  # Progress indicator
                        print(f"🎵 Received {audio_chunks_received} audio chunks...")

                elif event.type == "voice_stream_event_lifecycle":
                    lifecycle_events += 1
                    print(f"📋 Lifecycle event: {event.event}")

                elif event.type == "voice_stream_event_error":
                    print(f"❌ Error event: {event.error}")

            # Add 1 second of silence to ensure the audio finishes playing
            print("🔇 Adding silence buffer...")
            player.add_audio(np.zeros(24000 * 1, dtype=np.int16))

            print(f"\n✅ Voice interaction complete!")
            print(f"📊 Statistics:")
            print(f"   - Audio chunks played: {audio_chunks_received}")
            print(f"   - Lifecycle events: {lifecycle_events}")

    except KeyboardInterrupt:
        print("\n⏹️ Demo interrupted by user.")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
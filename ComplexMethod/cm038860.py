async def realtime_transcribe(audio_path: str, host: str, port: int, model: str):
    """
    Connect to the Realtime API and transcribe an audio file.
    """
    uri = f"ws://{host}:{port}/v1/realtime"

    async with websockets.connect(uri) as ws:
        # Wait for session.created
        response = json.loads(await ws.recv())
        if response["type"] == "session.created":
            print(f"Session created: {response['id']}")
        else:
            print(f"Unexpected response: {response}")
            return

        # Validate model
        await ws.send(json.dumps({"type": "session.update", "model": model}))

        # Signal ready to start
        await ws.send(json.dumps({"type": "input_audio_buffer.commit"}))

        # Convert audio file to base64 PCM16
        print(f"Loading audio from: {audio_path}")
        audio_base64 = audio_to_pcm16_base64(audio_path)

        # Send audio in chunks (4KB of raw audio = ~8KB base64)
        chunk_size = 4096
        audio_bytes = base64.b64decode(audio_base64)
        total_chunks = (len(audio_bytes) + chunk_size - 1) // chunk_size

        print(f"Sending {total_chunks} audio chunks...")
        for i in range(0, len(audio_bytes), chunk_size):
            chunk = audio_bytes[i : i + chunk_size]
            await ws.send(
                json.dumps(
                    {
                        "type": "input_audio_buffer.append",
                        "audio": base64.b64encode(chunk).decode("utf-8"),
                    }
                )
            )

        # Signal all audio is sent
        await ws.send(json.dumps({"type": "input_audio_buffer.commit", "final": True}))
        print("Audio sent. Waiting for transcription...\n")

        # Receive transcription
        print("Transcription: ", end="", flush=True)
        while True:
            response = json.loads(await ws.recv())
            if response["type"] == "transcription.delta":
                print(response["delta"], end="", flush=True)
            elif response["type"] == "transcription.done":
                print(f"\n\nFinal transcription: {response['text']}")
                if response.get("usage"):
                    print(f"Usage: {response['usage']}")
                break
            elif response["type"] == "error":
                print(f"\nError: {response['error']}")
                break
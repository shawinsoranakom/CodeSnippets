async def advanced_streaming_example():
    """Shows how to work with RunResultStreaming object"""

    print("\n=== Advanced Streaming with RunResultStreaming ===")
    print("Generating a long story with progress tracking...")

    # Track streaming progress
    events_count = 0
    chunks_received = []

    # Get the streaming result generator
    streaming_result = Runner.run_streamed(
        root_agent,
        "Write a creative short story about a robot who discovers emotions. Make it at least 500 words."
    )

    print("Processing streaming events:")

    async for event in streaming_result:
        events_count += 1

        # Collect content chunks
        if hasattr(event, 'content') and event.content:
            chunks_received.append(event.content)
            # Show progress every 10 chunks
            if len(chunks_received) % 10 == 0:
                print(f"\n[PROGRESS] Received {len(chunks_received)} chunks...")
            print(event.content, end='', flush=True)

        # Handle specific event types
        if hasattr(event, 'type'):
            if event.type == "tool_call_start":
                print(f"\n[EVENT] Tool call started")
            elif event.type == "tool_call_complete":
                print(f"\n[EVENT] Tool call completed")

    print(f"\n\nStreaming summary:")
    print(f"- Total events processed: {events_count}")
    print(f"- Content chunks received: {len(chunks_received)}")
    print(f"- Final story length: {sum(len(chunk) for chunk in chunks_received)} characters")

    # Access the final result
    final_result = "".join(chunks_received)
    return final_result
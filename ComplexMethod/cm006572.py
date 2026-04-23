async def test_multiple_events_with_queue(self):
        """Test sending multiple events to queue."""
        queue = asyncio.Queue()
        manager = create_default_event_manager(queue)

        # Send multiple events
        events_to_send = [("token", {"chunk": "hello"}), ("message", {"text": "world"}), ("end", {"status": "done"})]

        for event_type, data in events_to_send:
            manager.send_event(event_type=event_type, data=data)

        # Verify all events are in queue
        assert queue.qsize() == len(events_to_send)

        # Process all events
        received_events = []
        while not queue.empty():
            item = await queue.get()
            _, data_bytes, _ = item
            data_str = data_bytes.decode("utf-8").strip()
            parsed_data = json.loads(data_str)
            received_events.append((parsed_data["event"], parsed_data["data"]))

        # Verify all events were received correctly
        assert len(received_events) == len(events_to_send)
        for sent, received in zip(events_to_send, received_events, strict=False):
            assert sent[0] == received[0]  # event type
            assert sent[1] == received[1]
def get_new_cpu_stored_events(self) -> list[BlockStored]:
        cpu_stored_events: list[BlockStored] = []

        poller = zmq.Poller()
        poller.register(self.sub, zmq.POLLIN)

        poll_ms = _FIRST_EVENT_POLL_MS
        deadline = time.monotonic() + _EVENT_DRAIN_TIMEOUT
        while time.monotonic() < deadline:
            events = dict(poller.poll(poll_ms))

            if events.get(self.sub) != zmq.POLLIN:
                return cpu_stored_events

            topic_bytes, _, payload = self.sub.recv_multipart()

            assert topic_bytes == self.topic_bytes

            event_batch = self.decoder.decode(payload)
            assert isinstance(event_batch, KVEventBatch)
            for event in event_batch.events:
                if isinstance(event, BlockStored) and event.medium == "CPU":
                    cpu_stored_events.append(event)
                    poll_ms = 100

        return cpu_stored_events
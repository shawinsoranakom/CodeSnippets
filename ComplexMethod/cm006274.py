async def emit(self, flow_id: str, event_type: str, data: Any) -> None:
        """Emit an event to all subscribers of a flow.

        Args:
            flow_id: The flow ID to emit to
            event_type: Type of event (build_start, end_vertex, etc.)
            data: Event data (will be JSON serialized)
        """
        async with self._lock:
            listeners = self._listeners.get(flow_id, set()).copy()

        if not listeners:
            # No one listening, skip emission (performance optimization)
            return

        # Prepare event
        event = {
            "event": event_type,
            "data": data,
            "timestamp": time.time(),
        }

        # Send to all queues
        dead_queues: set[asyncio.Queue] = set()

        for queue in listeners:
            try:
                await asyncio.wait_for(queue.put(event), timeout=SSE_EMIT_TIMEOUT_SECONDS)
            except asyncio.TimeoutError:
                # Queue is full (slow consumer), skip this event
                logger.warning(f"Queue full for flow {flow_id}, dropping event {event_type}")
            except Exception as e:  # noqa: BLE001
                # Queue is closed or broken, mark for removal
                logger.error(f"Error putting event in queue for flow {flow_id}: {e}")
                dead_queues.add(queue)

        # Clean up dead queues
        if dead_queues:
            async with self._lock:
                if flow_id in self._listeners:
                    self._listeners[flow_id] -= dead_queues
                    if not self._listeners[flow_id]:
                        del self._listeners[flow_id]
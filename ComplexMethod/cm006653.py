def send_event(self, *, event_type: str, data: LoggableType):
        jsonable_data = jsonable_encoder(data)
        json_data = {"event": event_type, "data": jsonable_data}
        event_id = f"{event_type}-{uuid.uuid4()}"
        str_data = json.dumps(json_data) + "\n\n"
        if self.queue:
            try:
                item = (event_id, str_data.encode("utf-8"), time.time())
                try:
                    asyncio.get_running_loop()
                    in_event_loop = True
                except RuntimeError:
                    in_event_loop = False

                if in_event_loop:
                    # Called from within the event loop — safe to call directly
                    self.queue.put_nowait(item)
                elif self._loop is not None and self._loop.is_running():
                    # Called from a thread outside the event loop (e.g. sync tool in executor)
                    # Use call_soon_threadsafe so asyncio wakes up the queue getter properly
                    try:
                        self._loop.call_soon_threadsafe(self.queue.put_nowait, item)
                    except RuntimeError:
                        logger.warning(
                            "Event loop stopped before event could be scheduled; event_type=%s dropped", event_type
                        )
                else:
                    # Sync context with no event loop — call directly (e.g. unit tests)
                    self.queue.put_nowait(item)
            except asyncio.QueueFull:
                logger.warning("Event queue full; dropping event_type=%s", event_type)
            except Exception:  # noqa: BLE001
                logger.error("Unexpected error dispatching event_type=%s", event_type, exc_info=True)
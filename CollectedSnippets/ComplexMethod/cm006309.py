def get_since(self, flow_id: str, since: float) -> tuple[list[FlowEvent], bool]:
        """Return (events_after_since, settled).

        settled is True if:
        - No events exist for this flow, OR
        - A flow_settled event exists after `since`, OR
        - The most recent event is older than SETTLE_TIMEOUT seconds.
        """
        key = f"flow_events:{flow_id}"
        raw = self._cache.get(key, default=None)
        all_events = [FlowEvent(**e) for e in json.loads(raw)] if raw else []

        after = [e for e in all_events if e.timestamp > since]

        if not after and not all_events:
            return [], True

        if any(e.type == "flow_settled" for e in after):
            return after, True

        last_event_age = time.time() - all_events[-1].timestamp
        settled = last_event_age >= self.SETTLE_TIMEOUT

        return after, settled
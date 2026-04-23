def _supervisor_events_to_issues(self, event: dict[str, Any]) -> None:
        """Create issues from supervisor events."""
        if ATTR_WS_EVENT not in event:
            return

        if (
            event[ATTR_WS_EVENT] == EVENT_SUPERVISOR_UPDATE
            and event.get(ATTR_UPDATE_KEY) == UPDATE_KEY_SUPERVISOR
            and event.get(ATTR_DATA, {}).get(ATTR_STARTUP) == STARTUP_COMPLETE
        ):
            self._hass.async_create_task(self._update())

        elif event[ATTR_WS_EVENT] == EVENT_HEALTH_CHANGED:
            self.unhealthy_reasons = (
                set()
                if event[ATTR_DATA][ATTR_HEALTHY]
                else set(event[ATTR_DATA][ATTR_UNHEALTHY_REASONS])
            )

        elif event[ATTR_WS_EVENT] == EVENT_SUPPORTED_CHANGED:
            self.unsupported_reasons = (
                set()
                if event[ATTR_DATA][ATTR_SUPPORTED]
                else set(event[ATTR_DATA][ATTR_UNSUPPORTED_REASONS])
            )

        elif event[ATTR_WS_EVENT] == EVENT_ISSUE_CHANGED:
            self.add_issue(Issue.from_dict(event[ATTR_DATA]))

        elif event[ATTR_WS_EVENT] == EVENT_ISSUE_REMOVED:
            self.remove_issue(Issue.from_dict(event[ATTR_DATA]))
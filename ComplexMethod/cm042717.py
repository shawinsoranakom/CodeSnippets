def _handle_events(self, events: list[Event]) -> None:
        """Private method which acts as a bridge between the events
        received from the HTTP/2 data and IH2EventsHandler

        Arguments:
            events -- A list of events that the remote peer triggered by sending data
        """
        for event in events:
            if isinstance(event, ConnectionTerminated):
                self.connection_terminated(event)
            elif isinstance(event, DataReceived):
                self.data_received(event)
            elif isinstance(event, ResponseReceived):
                self.response_received(event)
            elif isinstance(event, StreamEnded):
                self.stream_ended(event)
            elif isinstance(event, StreamReset):
                self.stream_reset(event)
            elif isinstance(event, WindowUpdated):
                self.window_updated(event)
            elif isinstance(event, SettingsAcknowledged):
                self.settings_acknowledged(event)
            elif isinstance(event, UnknownFrameReceived):
                logger.warning("Unknown frame received: %s", event.frame)
def __init__(self, events: list[Event] | None):
        replay_events = []
        for event in events or []:
            if event.source == EventSource.ENVIRONMENT:
                # ignore ENVIRONMENT events as they are not issued by
                # the user or agent, and should not be replayed
                continue
            if isinstance(event, NullObservation):
                # ignore NullObservation
                continue
            replay_events.append(event)

        if replay_events:
            logger.info(f'Replay events loaded, events length = {len(replay_events)}')
            for index in range(len(replay_events) - 1):
                event = replay_events[index]
                if isinstance(event, MessageAction) and event.wait_for_response:
                    # For any message waiting for response that is not the last
                    # event, we override wait_for_response to False, as a response
                    # would have been included in the next event, and we don't
                    # want the user to interfere with the replay process
                    logger.info(
                        'Replay events contains wait_for_response message action, ignoring wait_for_response'
                    )
                    event.wait_for_response = False
        self.replay_events = replay_events
        self.replay_mode = bool(replay_events)
        self.replay_index = 0
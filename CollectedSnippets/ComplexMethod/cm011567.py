def _sanitize(self) -> None:
        state = self._state

        expire_time = datetime.now(timezone.utc) - (
            self._settings.keep_alive_interval * self._settings.keep_alive_max_attempt
        )

        # Filter out the dead nodes.
        self._dead_nodes = [
            node
            for node, last_heartbeat in state.last_heartbeats.items()
            if last_heartbeat < expire_time
        ]

        participant_removed = False

        for dead_node in self._dead_nodes:
            msg = f"Detected dead node '{dead_node}', removing it from the rendezvous"
            logger.debug(msg)
            del state.last_heartbeats[dead_node]

            try:
                del state.participants[dead_node]

                participant_removed = True
            except KeyError:
                pass

            try:
                state.wait_list.remove(dead_node)
            except KeyError:
                pass

            try:
                state.redundancy_list.remove(dead_node)
            except KeyError:
                pass

        if participant_removed:
            # Common epilogue shared with the _remove_from_participants()
            # function of _DistributedRendezvousOpExecutor.
            _remove_participant_epilogue(state, self._settings)
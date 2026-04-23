def statsd_event_listener(event):
        """Listen for new messages on the bus and sends them to StatsD."""
        if (state := event.data.get("new_state")) is None:
            return

        try:
            if value_mapping and state.state in value_mapping:
                _state = float(value_mapping[state.state])
            else:
                _state = state_helper.state_as_number(state)
        except ValueError:
            # Set the state to none and continue for any numeric attributes.
            _state = None

        states = dict(state.attributes)

        _LOGGER.debug("Sending %s", state.entity_id)

        if show_attribute_flag is True:
            if isinstance(_state, (float, int)):
                statsd_client.gauge(f"{state.entity_id}.state", _state, sample_rate)

            # Send attribute values
            for key, value in states.items():
                if isinstance(value, (float, int)):
                    stat = f"{state.entity_id}.{key.replace(' ', '_')}"
                    statsd_client.gauge(stat, value, sample_rate)

        elif isinstance(_state, (float, int)):
            statsd_client.gauge(state.entity_id, _state, sample_rate)

        # Increment the count
        statsd_client.incr(state.entity_id, rate=sample_rate)
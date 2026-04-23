def _write(self, record_type, records):
        if record_type.startswith(AIRBYTE_STREAM_RECORD_PREFIX):
            for record in records:
                payload = record.pop(AIRBYTE_DATA_RECORD_FIELD)
                self.on_event(payload)
        elif record_type == AIRBYTE_STATE_RECORD_TYPE:
            # Parse state according to the schema described in the protocol
            # https://docs.airbyte.com/understanding-airbyte/airbyte-protocol#airbytestatemessage
            for record in records:
                full_state = json.loads(record[AIRBYTE_DATA_RECORD_FIELD])
                state_type = full_state.get("type", "LEGACY")
                if state_type == "LEGACY":
                    self._handle_legacy_state(full_state)
                elif state_type == "GLOBAL":
                    self._handle_global_state(full_state)
                elif state_type == "STREAM" or state_type == "PER_STREAM":
                    # two different names in the docs, hence two clauses
                    self._handle_stream_state(full_state)
                else:
                    logging.warning(
                        f"Unknown state type: {state_type}. Ignoring state: {full_state}"
                    )
            self.on_state(self.get_state())
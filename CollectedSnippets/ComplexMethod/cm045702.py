def load(self, messages):
        self.job_started_at = datetime.datetime.utcnow().isoformat()
        self.slice_started_at = self.job_started_at
        buffer = []
        stream = None
        for message in messages:
            if message["type"] == "RECORD":
                new_stream = message["record"]["stream"]
                if new_stream != stream and stream is not None:
                    self._format_and_write(f"_airbyte_raw_{stream}", buffer)
                    buffer = []
                    self.slice_started_at = datetime.datetime.utcnow().isoformat()
                stream = new_stream
                buffer.append(message["record"])
                if len(buffer) > self.buffer_size_max:
                    self._format_and_write(f"_airbyte_raw_{stream}", buffer)
                    buffer = []
            elif message["type"] == "STATE":
                self._format_and_write(f"_airbyte_raw_{stream}", buffer)
                buffer = []
                self._format_and_write("_airbyte_states", [message["state"]])
                self.slice_started_at = datetime.datetime.utcnow().isoformat()
            elif message["type"] == "LOG":
                self._format_and_write("_airbyte_logs", [message["log"]])
            elif message["type"] == "TRACE":
                self._format_and_write("_airbyte_logs", [message["trace"]])
            else:
                raise NotImplementedError(
                    f'message type {message["type"]} is not managed yet'
                )
        self._format_and_write(f"_airbyte_raw_{stream}", buffer)
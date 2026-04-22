def get(self) -> None:
        stats = self._manager.get_stats()

        # If the request asked for protobuf output, we return a serialized
        # protobuf. Else we return text.
        if "application/x-protobuf" in self.request.headers.get_list("Accept"):
            self.write(self._stats_to_proto(stats).SerializeToString())
            self.set_header("Content-Type", "application/x-protobuf")
            self.set_status(200)
        else:
            self.write(self._stats_to_text(self._manager.get_stats()))
            self.set_header("Content-Type", "application/openmetrics-text")
            self.set_status(200)
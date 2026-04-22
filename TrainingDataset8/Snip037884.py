def get_debug(self) -> Dict[str, Any]:
        from google.protobuf.json_format import MessageToDict

        return {
            "queue": [MessageToDict(m) for m in self._queue],
            "ids": list(self._delta_index_map.keys()),
        }
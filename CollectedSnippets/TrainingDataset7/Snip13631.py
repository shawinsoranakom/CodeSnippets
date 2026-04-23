def _encode_json(self, data, content_type):
        """
        Return encoded JSON if data is a dict, list, or tuple and content_type
        is application/json.
        """
        should_encode = JSON_CONTENT_TYPE_RE.match(content_type) and isinstance(
            data, (dict, list, tuple)
        )
        return json.dumps(data, cls=self.json_encoder) if should_encode else data
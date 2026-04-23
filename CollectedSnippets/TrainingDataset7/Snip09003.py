def _get_lines(stream):
        for line in stream:
            if not line.strip():
                continue
            try:
                yield json.loads(line)
            except Exception as exc:
                raise DeserializationError() from exc
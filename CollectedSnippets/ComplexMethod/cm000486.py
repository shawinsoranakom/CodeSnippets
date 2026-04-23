def _scan(value: Any) -> None:
        if isinstance(value, str) and value.startswith("workspace://"):
            raw = value.removeprefix("workspace://")
            file_ref = raw.split("#", 1)[0] if "#" in raw else raw
            if file_ref and not file_ref.startswith("/"):
                file_ids.add(file_ref)
        elif isinstance(value, list):
            for item in value:
                _scan(item)
        elif isinstance(value, dict):
            for v in value.values():
                _scan(v)
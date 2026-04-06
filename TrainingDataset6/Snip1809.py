def _serialize_item(item: Any) -> bytes:
                    return _serialize_data(item) + b"\n"
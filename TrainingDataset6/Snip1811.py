def _sync_stream_jsonl() -> Iterator[bytes]:
                        for item in gen:  # ty: ignore[not-iterable]
                            yield _serialize_item(item)
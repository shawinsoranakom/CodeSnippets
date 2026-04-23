def _serialize_sse_item(item: Any) -> bytes:
                    if isinstance(item, ServerSentEvent):
                        # User controls the event structure.
                        # Serialize the data payload if present.
                        # For ServerSentEvent items we skip stream_item_field
                        # validation (the user may mix types intentionally).
                        if item.raw_data is not None:
                            data_str: str | None = item.raw_data
                        elif item.data is not None:
                            if hasattr(item.data, "model_dump_json"):
                                data_str = item.data.model_dump_json()
                            else:
                                data_str = json.dumps(jsonable_encoder(item.data))
                        else:
                            data_str = None
                        return format_sse_event(
                            data_str=data_str,
                            event=item.event,
                            id=item.id,
                            retry=item.retry,
                            comment=item.comment,
                        )
                    else:
                        # Plain object: validate + serialize via
                        # stream_item_field (if set) and wrap in data field
                        return format_sse_event(
                            data_str=_serialize_data(item).decode("utf-8")
                        )
def event_stream_serializer() -> Iterable[bytes]:
            yield self._encode_event_payload("initial-response")

            # create a default response
            serialized_event_response = self._create_default_response(operation_model, mime_type)
            # get the members of the event stream shape
            event_stream_shape_members = (
                event_stream_shape.members if event_stream_shape is not None else None
            )
            # extract the generator from the given response data
            event_generator = response.get(event_stream_member_name)
            if not isinstance(event_generator, Iterator):
                raise ProtocolSerializerError(
                    "Expected iterator for streaming event serialization."
                )

            # yield one event per generated event
            for event in event_generator:
                # find the actual event payload (the member with event=true)
                event_member_shape = None
                event_member_name = None
                for member_name, member_shape in event_stream_shape_members.items():
                    if member_shape.serialization.get("event") and member_name in event:
                        event_member_shape = member_shape
                        event_member_name = member_name
                        break
                if event_member_shape is None:
                    raise UnknownSerializerError("Couldn't find event shape for serialization.")

                # serialize the part of the response for the event
                self._serialize_response(
                    event.get(event_member_name),
                    serialized_event_response,
                    event_member_shape,
                    event_member_shape.members if event_member_shape is not None else None,
                    operation_model,
                    mime_type,
                    request_id,
                )
                # execute additional response traits (might be modifying the response)
                serialized_event_response = self._prepare_additional_traits_in_response(
                    serialized_event_response, operation_model, request_id
                )
                # encode the event and yield it
                yield self._encode_event_payload(
                    event_type=event_member_name, content=serialized_event_response.data
                )
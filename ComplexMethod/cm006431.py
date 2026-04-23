async def _stream_vertex(flow_id: str, vertex_id: str, chat_service: ChatService):
    graph = None
    try:
        try:
            cache = await chat_service.get_cache(flow_id)
        except Exception as exc:  # noqa: BLE001
            await logger.aexception("Error building Component")
            yield str(StreamData(event="error", data={"error": str(exc)}))
            return

        if isinstance(cache, CacheMiss):
            # If there's no cache
            msg = f"No cache found for {flow_id}."
            await logger.aerror(msg)
            yield str(StreamData(event="error", data={"error": msg}))
            return
        else:
            graph = cache.get("result")

        try:
            vertex: InterfaceVertex = graph.get_vertex(vertex_id)
        except Exception as exc:  # noqa: BLE001
            await logger.aexception("Error building Component")
            yield str(StreamData(event="error", data={"error": str(exc)}))
            return

        if not hasattr(vertex, "stream"):
            msg = f"Vertex {vertex_id} does not support streaming"
            await logger.aerror(msg)
            yield str(StreamData(event="error", data={"error": msg}))
            return

        if isinstance(vertex.built_result, str) and vertex.built_result:
            stream_data = StreamData(
                event="message",
                data={"message": f"Streaming vertex {vertex_id}"},
            )
            yield str(stream_data)
            stream_data = StreamData(
                event="message",
                data={"chunk": vertex.built_result},
            )
            yield str(stream_data)

        elif not vertex.frozen or not vertex.built:
            await logger.adebug(f"Streaming vertex {vertex_id}")
            stream_data = StreamData(
                event="message",
                data={"message": f"Streaming vertex {vertex_id}"},
            )
            yield str(stream_data)
            try:
                async for chunk in vertex.stream():
                    stream_data = StreamData(
                        event="message",
                        data={"chunk": chunk},
                    )
                    yield str(stream_data)
            except Exception as exc:  # noqa: BLE001
                await logger.aexception("Error building Component")
                exc_message = parse_exception(exc)
                if exc_message == "The message must be an iterator or an async iterator.":
                    exc_message = "This stream has already been closed."
                yield str(StreamData(event="error", data={"error": exc_message}))
        elif vertex.result is not None:
            stream_data = StreamData(
                event="message",
                data={"chunk": vertex.built_result},
            )
            yield str(stream_data)
        else:
            msg = f"No result found for vertex {vertex_id}"
            await logger.aerror(msg)
            yield str(StreamData(event="error", data={"error": msg}))
            return
    finally:
        await logger.adebug("Closing stream")
        if graph:
            await chat_service.set_cache(flow_id, graph)
        yield str(StreamData(event="close", data={"message": "Stream closed"}))
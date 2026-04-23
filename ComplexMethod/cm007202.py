async def stream(self):
        iterator = self.params.get(INPUT_FIELD_NAME, None)
        if not isinstance(iterator, AsyncIterator | Iterator):
            msg = "The message must be an iterator or an async iterator."
            raise TypeError(msg)
        is_async = isinstance(iterator, AsyncIterator)
        complete_message = ""
        if is_async:
            async for message in iterator:
                message_ = message.content if hasattr(message, "content") else message
                message_ = message_.text if hasattr(message_, "text") else message_
                yield message_
                complete_message += message_
        else:
            for message in iterator:
                message_ = message.content if hasattr(message, "content") else message
                message_ = message_.text if hasattr(message_, "text") else message_
                yield message_
                complete_message += message_

        files = self.params.get("files", [])

        treat_file_path = files is not None and not isinstance(files, list) and isinstance(files, str)
        if treat_file_path:
            self.params["files"] = rewrite_file_path(files)

        if hasattr(self.params.get("sender_name"), "get_text"):
            sender_name = self.params.get("sender_name").get_text()
        else:
            sender_name = self.params.get("sender_name")
        self.artifacts = ChatOutputResponse(
            message=complete_message,
            sender=self.params.get("sender", ""),
            sender_name=sender_name,
            files=[{"path": file} if isinstance(file, str) else file for file in self.params.get("files", [])],
            type=ArtifactType.OBJECT.value,
        ).model_dump()

        message = await Message.create(
            text=complete_message,
            sender=self.params.get("sender", ""),
            sender_name=self.params.get("sender_name", ""),
            files=self.params.get("files", []),
            flow_id=self.graph.flow_id,
            session_id=self.params.get("session_id", ""),
        )
        self.params[INPUT_FIELD_NAME] = complete_message
        if isinstance(self.built_object, dict):
            for key, value in self.built_object.items():
                if hasattr(value, "text") and (isinstance(value.text, AsyncIterator | Iterator) or value.text == ""):
                    self.built_object[key] = message
        else:
            self.built_object = message
            self.artifacts_type = ArtifactType.MESSAGE

        # Update artifacts with the message
        # and remove the stream_url
        self.finalize_build()
        await logger.adebug(f"Streamed message: {complete_message}")
        # Set the result in the vertex of origin
        edges = self.get_edge_with_target(self.id)
        for edge in edges:
            origin_vertex = self.graph.get_vertex(edge.source_id)
            for key, value in origin_vertex.results.items():
                if isinstance(value, AsyncIterator | Iterator):
                    origin_vertex.results[key] = complete_message
        if (
            self.custom_component
            and hasattr(self.custom_component, "should_store_message")
            and hasattr(self.custom_component, "store_message")
        ):
            await self.custom_component.store_message(message)
        await log_vertex_build(
            flow_id=self.graph.flow_id,
            vertex_id=self.id,
            valid=True,
            params=self.built_object_repr(),
            data=self.result,
            artifacts=self.artifacts,
        )

        self._validate_built_object()
        self.built = True
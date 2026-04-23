async def astep(
        self,
        inputs: InputValueRequest | None = None,
        files: list[str] | None = None,
        user_id: str | None = None,
        event_manager: EventManager | None = None,
    ):
        if not self._prepared:
            msg = "Graph not prepared. Call prepare() first."
            raise ValueError(msg)
        if not self._run_queue:
            self._end_all_traces_async()
            return Finish()
        vertex_id = self.get_next_in_queue()
        if not vertex_id:
            msg = "No vertex to run"
            raise ValueError(msg)

        # Emit build_start event before building vertex
        if event_manager is not None:
            event_manager.on_build_start(data={"id": vertex_id})

        chat_service = get_chat_service()

        # Provide fallback cache functions if chat service is unavailable
        if chat_service is not None:
            get_cache_func = chat_service.get_cache
            set_cache_func = chat_service.set_cache
        else:
            # Fallback no-op cache functions for tests or when service unavailable
            async def get_cache_func(*args, **kwargs):  # noqa: ARG001
                return CacheMiss()

            async def set_cache_func(*args, **kwargs) -> bool:  # noqa: ARG001
                return True

        vertex_build_result = await self.build_vertex(
            vertex_id=vertex_id,
            user_id=user_id,
            inputs_dict=inputs.model_dump() if inputs and hasattr(inputs, "model_dump") else {},
            files=files,
            get_cache=get_cache_func,
            set_cache=set_cache_func,
            event_manager=event_manager,
        )

        next_runnable_vertices = await self.get_next_runnable_vertices(
            self.lock, vertex=vertex_build_result.vertex, cache=False
        )
        if self.stop_vertex and self.stop_vertex in next_runnable_vertices:
            next_runnable_vertices = [self.stop_vertex]
        self.extend_run_queue(next_runnable_vertices)
        self.reset_inactivated_vertices()
        self.reset_activated_vertices()

        if chat_service is not None:
            await chat_service.set_cache(str(self.flow_id or self._run_id), self)
        self._record_snapshot(vertex_id)
        return vertex_build_result
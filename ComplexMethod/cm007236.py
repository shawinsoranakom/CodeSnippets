async def build_vertex(
        self,
        vertex_id: str,
        *,
        get_cache: GetCache | None = None,
        set_cache: SetCache | None = None,
        inputs_dict: dict[str, str] | None = None,
        files: list[str] | None = None,
        user_id: str | None = None,
        fallback_to_env_vars: bool = False,
        event_manager: EventManager | None = None,
    ) -> VertexBuildResult:
        """Builds a vertex in the graph.

        Args:
            vertex_id (str): The ID of the vertex to build.
            get_cache (GetCache): A coroutine to get the cache.
            set_cache (SetCache): A coroutine to set the cache.
            inputs_dict (Optional[Dict[str, str]]): Optional dictionary of inputs for the vertex. Defaults to None.
            files: (Optional[List[str]]): Optional list of files. Defaults to None.
            user_id (Optional[str]): Optional user ID. Defaults to None.
            fallback_to_env_vars (bool): Whether to fallback to environment variables. Defaults to False.
            event_manager (Optional[EventManager]): Optional event manager. Defaults to None.

        Returns:
            Tuple: A tuple containing the next runnable vertices, top level vertices, result dictionary,
            parameters, validity flag, artifacts, and the built vertex.

        Raises:
            ValueError: If no result is found for the vertex.
        """
        vertex = self.get_vertex(vertex_id)
        self.run_manager.add_to_vertices_being_run(vertex_id)
        try:
            params = ""
            should_build = False
            # Loop components must always build, even when frozen,
            # because they need to iterate through their data
            is_loop_component = vertex.display_name == "Loop" or vertex.is_loop
            if not vertex.frozen or is_loop_component:
                should_build = True
            else:
                # Check the cache for the vertex
                if get_cache is not None:
                    cached_result = await get_cache(key=vertex.id)
                else:
                    cached_result = CacheMiss()
                if isinstance(cached_result, CacheMiss):
                    should_build = True
                else:
                    try:
                        cached_vertex_dict = cached_result["result"]
                        # Now set update the vertex with the cached vertex
                        vertex.built = cached_vertex_dict["built"]
                        vertex.artifacts = cached_vertex_dict["artifacts"]
                        vertex.built_object = cached_vertex_dict["built_object"]
                        vertex.built_result = cached_vertex_dict["built_result"]
                        vertex.full_data = cached_vertex_dict["full_data"]
                        vertex.results = cached_vertex_dict["results"]
                        try:
                            vertex.finalize_build()

                            if vertex.result is not None:
                                vertex.result.used_frozen_result = True
                        except Exception:  # noqa: BLE001
                            logger.debug("Error finalizing build", exc_info=True)
                            vertex.built = False
                            should_build = True
                    except KeyError:
                        vertex.built = False
                        should_build = True

            if should_build:
                await vertex.build(
                    user_id=user_id,
                    inputs=inputs_dict,
                    fallback_to_env_vars=fallback_to_env_vars,
                    files=files,
                    event_manager=event_manager,
                )
                if set_cache is not None:
                    vertex_dict = {
                        "built": vertex.built,
                        "results": vertex.results,
                        "artifacts": vertex.artifacts,
                        "built_object": vertex.built_object,
                        "built_result": vertex.built_result,
                        "full_data": vertex.full_data,
                    }

                    await set_cache(key=vertex.id, data=vertex_dict)

        except Exception as exc:
            if not isinstance(exc, ComponentBuildError):
                await logger.aexception("Error building Component")
            raise

        if vertex.result is not None:
            params = f"{vertex.built_object_repr()}{params}"
            valid = True
            result_dict = vertex.result
            artifacts = vertex.artifacts
        else:
            msg = f"Error building Component: no result found for vertex {vertex_id}"
            raise ValueError(msg)

        return VertexBuildResult(
            result_dict=result_dict, params=params, valid=valid, artifacts=artifacts, vertex=vertex
        )
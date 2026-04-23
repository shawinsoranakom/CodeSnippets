async def _build_vertex(vertex_id: str, graph: Graph, event_manager: EventManager) -> VertexBuildResponse:
        flow_id_str = str(flow_id)
        next_runnable_vertices = []
        top_level_vertices = []
        start_time = time.perf_counter()
        error_message = None

        try:
            vertex = graph.get_vertex(vertex_id)
            try:
                lock = chat_service.async_cache_locks[flow_id_str]
                vertex_build_result = await graph.build_vertex(
                    vertex_id=vertex_id,
                    user_id=str(current_user.id),
                    inputs_dict=inputs.model_dump() if inputs else {},
                    files=files,
                    get_cache=chat_service.get_cache,
                    set_cache=chat_service.set_cache,
                    event_manager=event_manager,
                )
                result_dict = vertex_build_result.result_dict
                params = vertex_build_result.params
                valid = vertex_build_result.valid
                artifacts = vertex_build_result.artifacts
                next_runnable_vertices = await graph.get_next_runnable_vertices(lock, vertex=vertex, cache=False)
                top_level_vertices = graph.get_top_level_vertices(next_runnable_vertices)

                result_data_response = ResultDataResponse.model_validate(result_dict, from_attributes=True)
            except Exception as exc:  # noqa: BLE001
                if isinstance(exc, ComponentBuildError):
                    params = exc.message
                    tb = exc.formatted_traceback
                else:
                    tb = traceback.format_exc()
                    await logger.aexception("Error building Component")
                    params = format_exception_message(exc)
                message = {"errorMessage": params, "stackTrace": tb}
                valid = False
                error_message = params
                output_label = vertex.outputs[0]["name"] if vertex.outputs else "output"
                outputs = {output_label: OutputValue(message=message, type="error")}
                result_data_response = ResultDataResponse(results={}, outputs=outputs)
                artifacts = {}
                background_tasks.add_task(graph.end_all_traces_in_context(error=exc))

            result_data_response.message = artifacts

            # Log the vertex build
            if not vertex.will_stream and log_builds:
                background_tasks.add_task(
                    log_vertex_build,
                    flow_id=flow_id_str,
                    vertex_id=vertex_id,
                    valid=valid,
                    params=params,
                    data=result_data_response,
                    artifacts=artifacts,
                )
            else:
                await chat_service.set_cache(flow_id_str, graph)

            timedelta = time.perf_counter() - start_time

            duration = format_elapsed_time(timedelta)
            result_data_response.duration = duration
            result_data_response.timedelta = timedelta
            vertex.add_build_time(timedelta)
            # Capture both inactivated and conditionally excluded vertices
            inactivated_vertices = list(graph.inactivated_vertices.union(graph.conditionally_excluded_vertices))
            graph.reset_inactivated_vertices()
            graph.reset_activated_vertices()

            # Note: Do not reset conditionally_excluded_vertices each iteration
            # This is handled by the ConditionalRouter component

            # graph.stop_vertex tells us if the user asked
            # to stop the build of the graph at a certain vertex
            # if it is in next_vertices_ids, we need to remove other
            # vertices from next_vertices_ids
            if graph.stop_vertex and graph.stop_vertex in next_runnable_vertices:
                next_runnable_vertices = [graph.stop_vertex]

            if not graph.run_manager.vertices_being_run and not next_runnable_vertices:
                background_tasks.add_task(graph.end_all_traces_in_context())

            build_response = VertexBuildResponse(
                inactivated_vertices=list(set(inactivated_vertices)),
                next_vertices_ids=list(set(next_runnable_vertices)),
                top_level_vertices=list(set(top_level_vertices)),
                valid=valid,
                params=params,
                id=vertex.id,
                data=result_data_response,
            )

            # Extract and send component input telemetry (separate payload)
            _log_component_input_telemetry(vertex, vertex_id, graph.run_id, background_tasks, telemetry_service)

            # Send component execution telemetry
            background_tasks.add_task(
                telemetry_service.log_package_component,
                ComponentPayload(
                    component_name=vertex_id.split("-")[0],
                    component_id=vertex_id,
                    component_seconds=int(time.perf_counter() - start_time),
                    component_success=valid,
                    component_error_message=error_message,
                    component_run_id=graph.run_id,
                ),
            )
        except Exception as exc:
            if "vertex" in locals():
                # Extract and send component input telemetry even on error (separate payload)
                _log_component_input_telemetry(vertex, vertex_id, graph.run_id, background_tasks, telemetry_service)

            # Send component execution telemetry (error case)
            background_tasks.add_task(
                telemetry_service.log_package_component,
                ComponentPayload(
                    component_name=vertex_id.split("-")[0],
                    component_id=vertex_id,
                    component_seconds=int(time.perf_counter() - start_time),
                    component_success=False,
                    component_error_message=str(exc),
                    component_run_id=graph.run_id,
                ),
            )
            await logger.aexception("Error building Component")
            message = parse_exception(exc)
            raise HTTPException(status_code=500, detail=message) from exc

        return build_response
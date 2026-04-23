async def _execute_tasks(
        self, tasks: list[asyncio.Task], lock: asyncio.Lock, *, has_webhook_component: bool = False
    ) -> list[str]:
        """Executes tasks in parallel, handling exceptions for each task.

        Args:
            tasks: List of tasks to execute
            lock: Async lock for synchronization
            has_webhook_component: Whether the graph has a webhook component
        """
        from lfx.graph.utils import emit_vertex_build_event

        results = []
        completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)
        vertices: list[Vertex] = []
        # Store build results for SSE emission after calculating next_runnable_vertices
        build_results: dict[str, VertexBuildResult] = {}

        for i, result in enumerate(completed_tasks):
            task_name = tasks[i].get_name()
            vertex_id = tasks[i].get_name().split(" ")[0]

            if isinstance(result, Exception):
                await logger.aerror(f"Task {task_name} failed with exception: {result}")
                if has_webhook_component:
                    await self._log_vertex_build_from_exception(vertex_id, result)

                # Cancel all remaining tasks
                for t in tasks[i + 1 :]:
                    t.cancel()
                raise result
            if isinstance(result, VertexBuildResult):
                if self.flow_id is not None:
                    await log_vertex_build(
                        flow_id=self.flow_id,
                        vertex_id=result.vertex.id,
                        valid=result.valid,
                        params=result.params,
                        data=result.result_dict,
                        artifacts=result.artifacts,
                        job_id=self._run_id if self._run_id else None,
                    )
                    # Store for SSE emission later
                    build_results[result.vertex.id] = result

                vertices.append(result.vertex)
            else:
                msg = f"Invalid result from task {task_name}: {result}"
                raise TypeError(msg)

        for v in vertices:
            # set all executed vertices as non-runnable to not run them again.
            # they could be calculated as predecessor or successors of parallel vertices
            # This could usually happen with input vertices like ChatInput
            self.run_manager.remove_vertex_from_runnables(v.id)

            await logger.adebug(f"Vertex {v.id}, result: {v.built_result}, object: {v.built_object}")

        for v in vertices:
            next_runnable_vertices = await self.get_next_runnable_vertices(lock, vertex=v, cache=False)
            results.extend(next_runnable_vertices)

            # Emit SSE event with complete data including next_vertices_ids
            if self.flow_id is not None and v.id in build_results:
                build_result = build_results[v.id]
                # Get top level vertices for these next runnable vertices
                top_level = self.get_top_level_vertices(next_runnable_vertices)
                # Get inactivated vertices
                inactivated = list(self.inactivated_vertices.union(self.conditionally_excluded_vertices))

                await emit_vertex_build_event(
                    flow_id=self.flow_id,
                    vertex_id=v.id,
                    valid=build_result.valid,
                    params=build_result.params,
                    data_dict=build_result.result_dict,
                    artifacts_dict=build_result.artifacts,
                    next_vertices_ids=next_runnable_vertices,
                    top_level_vertices=top_level,
                    inactivated_vertices=inactivated,
                )

        return list(set(results))
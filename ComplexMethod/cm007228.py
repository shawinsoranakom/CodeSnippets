async def async_start(
        self,
        inputs: list[dict] | None = None,
        max_iterations: int | None = None,
        config: StartConfigDict | None = None,
        event_manager: EventManager | None = None,
        *,
        reset_output_values: bool = True,
    ):
        # Preserve start_component_id from constructor if available
        start_component_id = self._start.get_id() if self._start else None
        self.prepare(start_component_id=start_component_id)
        if reset_output_values:
            self._reset_all_output_values()

        await self.initialize_run()

        # The idea is for this to return a generator that yields the result of
        # each step call and raise StopIteration when the graph is done
        if config is not None:
            self.__apply_config(config)
        # I want to keep a counter of how many tyimes result.vertex.id
        # has been yielded
        yielded_counts: dict[str, int] = defaultdict(int)

        while should_continue(yielded_counts, max_iterations):
            result = await self.astep(event_manager=event_manager, inputs=inputs)
            yield result
            if isinstance(result, Finish):
                return
            if hasattr(result, "vertex"):
                yielded_counts[result.vertex.id] += 1
                # Emit on_end_vertex event for each completed vertex
                if event_manager is not None:
                    result_data_dict = None
                    if hasattr(result, "result_dict") and result.result_dict:
                        try:
                            result_data_dict = result.result_dict.model_dump()
                        except (AttributeError, TypeError):
                            result_data_dict = result.result_dict
                    build_data = {
                        "id": result.vertex.id,
                        "valid": result.valid if hasattr(result, "valid") else True,
                        "data": result_data_dict,
                    }
                    event_manager.on_end_vertex(data={"build_data": build_data})

        msg = "Max iterations reached"
        raise ValueError(msg)
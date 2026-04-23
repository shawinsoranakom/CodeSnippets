def reduce_scatter(
        self,
        step: str,
        map_fun: Callable[[], T],
        reduce_fun: Callable[[list[T]], list[R]],
    ) -> R:
        """
        Compute a value on each rank, then do centralized reduce on a single rank, followed by a scatter.

        This method operates in the following way:
            Run ``map_fun`` on all ranks
            Gather results on rank 0
            Call ``reduce_fun`` on all those values
            Scatter to each rank part of the result.
        """
        local_data: WRAPPED_EXCEPTION | T
        try:
            local_data = map_fun()
        except BaseException as e:
            local_data = _wrap_exception(e)

        all_data = self.gather_object(local_data)
        all_results: list[R | CheckpointException] | None = None
        if self.is_coordinator:
            if all_data is None:
                raise AssertionError("all_data is None")
            node_failures = _get_failure_dict(all_data)

            if len(node_failures) == 0:
                try:
                    # N.B. why can't mypy cast List[R] to List[Union[R, WRAPPED_EXCEPTION]]?
                    all_results = cast(
                        list[R | CheckpointException],
                        reduce_fun(cast(list[T], all_data)),
                    )
                except BaseException as e:
                    node_failures[self.rank] = _wrap_exception(e)

            if len(node_failures) > 0:
                all_results = [
                    CheckpointException(step, node_failures)
                ] * self.get_world_size()

        result = self.scatter_object(all_results)
        if isinstance(result, CheckpointException):
            raise result
        return result
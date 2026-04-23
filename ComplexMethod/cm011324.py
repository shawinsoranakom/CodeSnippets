def all_reduce(
        self,
        step: str,
        map_fun: Callable[[], T],
        reduce_fun: Callable[[list[T]], R],
    ) -> R:
        """
        Compute a value on each rank, then do centralized reduce on a single rank, followed by a broadcast.

        This method operates in the following way:
            Run ``map_fun`` on all ranks
            Gather results on rank 0
            Call ``reduce_fun`` on all those values
            Broadcast the reduced value to all ranks.
        """
        local_data: T | WRAPPED_EXCEPTION
        try:
            local_data = map_fun()
        except BaseException as e:
            local_data = _wrap_exception(e)

        all_data = self.gather_object(local_data)
        result: R | CheckpointException | None = None
        if self.is_coordinator:
            if all_data is None:
                raise AssertionError("all_data is None")
            node_failures = _get_failure_dict(all_data)
            if len(node_failures) == 0:
                try:
                    result = reduce_fun(cast(list[T], all_data))
                except BaseException as e:
                    node_failures[self.rank] = _wrap_exception(e)

            if len(node_failures) > 0:
                result = CheckpointException(step, node_failures)

        # pyrefly: ignore [bad-argument-type]
        final_result = self.broadcast_object(result)
        if isinstance(final_result, CheckpointException):
            raise final_result
        # pyrefly: ignore [redundant-cast]
        return cast(R, final_result)
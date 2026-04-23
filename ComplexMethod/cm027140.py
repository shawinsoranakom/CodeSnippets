def get_many(
        self,
        event_types: Iterable[EventType[Any] | str],
        session: Session,
        from_recorder: bool = False,
    ) -> dict[EventType[Any] | str, int | None]:
        """Resolve event_types to event_type_ids.

        This call is not thread-safe and must be called from the
        recorder thread.
        """
        results: dict[EventType[Any] | str, int | None] = {}
        missing: list[EventType[Any] | str] = []
        non_existent: list[EventType[Any] | str] = []

        for event_type in event_types:
            if (event_type_id := self._id_map.get(event_type)) is None:
                if event_type in self._non_existent_event_types:
                    results[event_type] = None
                else:
                    missing.append(event_type)

            results[event_type] = event_type_id

        if not missing:
            return results

        with session.no_autoflush:
            for missing_chunk in chunked_or_all(missing, self.recorder.max_bind_vars):
                for event_type_id, event_type in execute_stmt_lambda_element(
                    session, find_event_type_ids(missing_chunk), orm_rows=False
                ):
                    results[event_type] = self._id_map[event_type] = cast(
                        int, event_type_id
                    )

        if non_existent := [
            event_type for event_type in missing if results[event_type] is None
        ]:
            if from_recorder:
                # We are already in the recorder thread so we can update the
                # non-existent event types directly.
                for event_type in non_existent:
                    self._non_existent_event_types[event_type] = None
            else:
                # Queue a task to refresh the event types since its not
                # thread-safe to do it here since we are not in the recorder
                # thread.
                self.recorder.queue_task(RefreshEventTypesTask(non_existent))

        return results
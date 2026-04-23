def _table_from_dict(
        self,
        batches: dict[int, dict[int, list[tuple[int, api.Pointer, list[api.Value]]]]],
        schema: type[Schema],
        _stacklevel: int = 1,
    ) -> Table:
        """A function that creates a table from a mapping of timestamps to batches. Each batch
        is a mapping from worker id to list of rows processed in this batch by this worker,
        and each row is tuple (diff, key, values).

        Note: unless you need to specify timestamps and keys, consider using
        `table_from_list_of_batches` and `table_from_list_of_batches_by_workers`.

        Args:
            batches: dictionary with specified batches to be put in the table
            schema: schema of the table
        """
        unique_name = self._get_next_unique_name()
        workers = {worker for batch in batches.values() for worker in batch}
        for worker in workers:
            self.events[(unique_name, worker)] = []

        timestamps = set(batches.keys())

        if any(timestamp for timestamp in timestamps if timestamp < 0):
            raise ValueError("negative timestamp cannot be used")
        elif any(timestamp for timestamp in timestamps if timestamp == 0):
            warn(
                "rows with timestamp 0 are only backfilled and are not processed by output connectors"
            )

        if any(timestamp for timestamp in timestamps if timestamp % 2 == 1):
            warn(
                "timestamps are required to be even; all timestamps will be doubled",
                stacklevel=_stacklevel + 1,
            )
            batches = {2 * timestamp: batches[timestamp] for timestamp in batches}

        for timestamp in sorted(batches):
            self._advance_time_for_all_workers(unique_name, workers, timestamp)
            batch = batches[timestamp]
            for worker, changes in batch.items():
                for diff, key, values in changes:
                    if diff == 1:
                        event = api.SnapshotEvent.insert(key, values)
                        self.events[(unique_name, worker)] += [event] * diff
                    elif diff == -1:
                        event = api.SnapshotEvent.delete(key, values)
                        self.events[(unique_name, worker)] += [event] * (-diff)
                    else:
                        raise ValueError("only diffs of 1 and -1 are supported")

        return read(
            _EmptyConnectorSubject(datasource_name="debug.stream-generator"),
            name=unique_name,
            schema=schema,
        )
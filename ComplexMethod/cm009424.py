def _on_run_create(self, run: Run) -> None:
        """Start a run."""
        if self.root_id is None:
            self.root_id = run.id
            if not self.send(
                {
                    "op": "replace",
                    "path": "",
                    "value": RunState(
                        id=str(run.id),
                        streamed_output=[],
                        final_output=None,
                        logs={},
                        name=run.name,
                        type=run.run_type,
                    ),
                }
            ):
                return

        if not self.include_run(run):
            return

        # Determine previous index, increment by 1
        with self.lock:
            self._counter_map_by_name[run.name] += 1
            count = self._counter_map_by_name[run.name]
            self._key_map_by_run_id[run.id] = (
                run.name if count == 1 else f"{run.name}:{count}"
            )

        entry = LogEntry(
            id=str(run.id),
            name=run.name,
            type=run.run_type,
            tags=run.tags or [],
            metadata=(run.extra or {}).get("metadata", {}),
            start_time=run.start_time.isoformat(timespec="milliseconds"),
            streamed_output=[],
            streamed_output_str=[],
            final_output=None,
            end_time=None,
        )

        if self._schema_format == "streaming_events":
            # If using streaming events let's add inputs as well
            entry["inputs"] = _get_standardized_inputs(run, self._schema_format)

        # Add the run to the stream
        self.send(
            {
                "op": "add",
                "path": f"/logs/{self._key_map_by_run_id[run.id]}",
                "value": entry,
            }
        )
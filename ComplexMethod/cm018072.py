def override_syrupy_finish(self: SnapshotSession) -> int:
    """Override the finish method to allow for custom handling."""
    exitstatus = 0
    self.flush_snapshot_write_queue()
    self.report = SnapshotReport(
        base_dir=self.pytest_session.config.rootpath,
        collected_items=self._collected_items,
        selected_items=self._selected_items,
        assertions=self._assertions,
        options=self.pytest_session.config.option,
    )

    needs_xdist_merge = self.update_snapshots or bool(
        self.pytest_session.config.option.include_snapshot_details
    )

    if is_xdist_worker():
        if not needs_xdist_merge:
            return exitstatus
        with open(".pytest_syrupy_worker_count", "w", encoding="utf-8") as f:
            f.write(os.getenv("PYTEST_XDIST_WORKER_COUNT"))
        with open(
            f".pytest_syrupy_{os.getenv('PYTEST_XDIST_WORKER')}_result",
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(
                _serialize_report(
                    self.report, self._collected_items, self._selected_items
                ),
                f,
                indent=2,
            )
        return exitstatus
    if is_xdist_controller():
        return exitstatus

    if needs_xdist_merge:
        worker_count = None
        try:
            with open(".pytest_syrupy_worker_count", encoding="utf-8") as f:
                worker_count = f.read()
            os.remove(".pytest_syrupy_worker_count")
        except FileNotFoundError:
            pass

        if worker_count:
            for i in range(int(worker_count)):
                with open(f".pytest_syrupy_gw{i}_result", encoding="utf-8") as f:
                    _merge_serialized_report(self.report, json.load(f))
                os.remove(f".pytest_syrupy_gw{i}_result")

    if self.report.num_unused:
        if self.update_snapshots:
            self.remove_unused_snapshots(
                unused_snapshot_collections=self.report.unused,
                used_snapshot_collections=self.report.used,
            )
        elif not self.warn_unused_snapshots:
            exitstatus |= EXIT_STATUS_FAIL_UNUSED
    return exitstatus
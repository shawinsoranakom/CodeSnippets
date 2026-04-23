def _run_fast_phase(self, roots: tuple[RootType, ...]) -> tuple[int, int, int]:
        """Run phase 1: fast scan to create stub records.

        Returns:
            Tuple of (total_created, skipped_existing, total_paths)
        """
        t_fast_start = time.perf_counter()
        total_created = 0
        skipped_existing = 0

        existing_paths: set[str] = set()
        t_sync = time.perf_counter()
        for r in roots:
            if self._check_pause_and_cancel():
                return total_created, skipped_existing, 0
            existing_paths.update(sync_root_safely(r))
        logging.debug(
            "Fast scan: sync_root phase took %.3fs (%d existing paths)",
            time.perf_counter() - t_sync,
            len(existing_paths),
        )

        if self._check_pause_and_cancel():
            return total_created, skipped_existing, 0

        t_collect = time.perf_counter()
        paths = collect_paths_for_roots(roots)
        logging.debug(
            "Fast scan: collect_paths took %.3fs (%d paths found)",
            time.perf_counter() - t_collect,
            len(paths),
        )
        total_paths = len(paths)
        self._update_progress(total=total_paths)

        self._emit_event(
            "assets.seed.started",
            {"roots": list(roots), "total": total_paths, "phase": "fast"},
        )

        # Use stub specs (no metadata extraction, no hashing)
        t_specs = time.perf_counter()
        specs, tag_pool, skipped_existing = build_asset_specs(
            paths,
            existing_paths,
            enable_metadata_extraction=False,
            compute_hashes=False,
        )
        logging.debug(
            "Fast scan: build_asset_specs took %.3fs (%d specs, %d skipped)",
            time.perf_counter() - t_specs,
            len(specs),
            skipped_existing,
        )
        self._update_progress(skipped=skipped_existing)

        if self._check_pause_and_cancel():
            return total_created, skipped_existing, total_paths

        batch_size = 500
        last_progress_time = time.perf_counter()
        progress_interval = 1.0

        for i in range(0, len(specs), batch_size):
            if self._check_pause_and_cancel():
                logging.info(
                    "Fast scan cancelled after %d/%d files (created=%d)",
                    i,
                    len(specs),
                    total_created,
                )
                return total_created, skipped_existing, total_paths

            batch = specs[i : i + batch_size]
            batch_tags = {t for spec in batch for t in spec["tags"]}
            try:
                created = insert_asset_specs(batch, batch_tags)
                total_created += created
            except Exception as e:
                self._add_error(f"Batch insert failed at offset {i}: {e}")
                logging.exception("Batch insert failed at offset %d", i)

            scanned = i + len(batch)
            now = time.perf_counter()
            self._update_progress(scanned=scanned, created=total_created)

            if now - last_progress_time >= progress_interval:
                self._emit_event(
                    "assets.seed.progress",
                    {
                        "phase": "fast",
                        "scanned": scanned,
                        "total": len(specs),
                        "created": total_created,
                    },
                )
                last_progress_time = now

        self._update_progress(scanned=len(specs), created=total_created)
        logging.info(
            "Fast scan complete: %.3fs total (created=%d, skipped=%d, total_paths=%d)",
            time.perf_counter() - t_fast_start,
            total_created,
            skipped_existing,
            total_paths,
        )
        return total_created, skipped_existing, total_paths
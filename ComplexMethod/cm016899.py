def _run_enrich_phase(self, roots: tuple[RootType, ...]) -> tuple[bool, int]:
        """Run phase 2: enrich existing records with metadata and hashes.

        Returns:
            Tuple of (cancelled, total_enriched)
        """
        total_enriched = 0
        batch_size = 100
        last_progress_time = time.perf_counter()
        progress_interval = 1.0

        # Get the target enrichment level based on compute_hashes
        if not self._compute_hashes:
            target_max_level = ENRICHMENT_STUB
        else:
            target_max_level = ENRICHMENT_METADATA

        self._emit_event(
            "assets.seed.started",
            {"roots": list(roots), "phase": "enrich"},
        )

        skip_ids: set[str] = set()
        consecutive_empty = 0
        max_consecutive_empty = 3

        # Hash checkpoints survive across batches so interrupted hashes
        # can be resumed without re-reading the entire file.
        hash_checkpoints: dict[str, object] = {}

        while True:
            if self._check_pause_and_cancel():
                logging.info("Enrich scan cancelled after %d assets", total_enriched)
                return True, total_enriched

            # Fetch next batch of unenriched assets
            unenriched = get_unenriched_assets_for_roots(
                roots,
                max_level=target_max_level,
                limit=batch_size,
            )

            # Filter out previously failed references
            if skip_ids:
                unenriched = [r for r in unenriched if r.reference_id not in skip_ids]

            if not unenriched:
                break

            enriched, failed_ids = enrich_assets_batch(
                unenriched,
                extract_metadata=True,
                compute_hash=self._compute_hashes,
                interrupt_check=self._is_paused_or_cancelled,
                hash_checkpoints=hash_checkpoints,
            )
            total_enriched += enriched
            skip_ids.update(failed_ids)

            if enriched == 0:
                consecutive_empty += 1
                if consecutive_empty >= max_consecutive_empty:
                    logging.warning(
                        "Enrich phase stopping: %d consecutive batches with no progress (%d skipped)",
                        consecutive_empty,
                        len(skip_ids),
                    )
                    break
            else:
                consecutive_empty = 0

            now = time.perf_counter()
            if now - last_progress_time >= progress_interval:
                self._emit_event(
                    "assets.seed.progress",
                    {
                        "phase": "enrich",
                        "enriched": total_enriched,
                    },
                )
                last_progress_time = now

        return False, total_enriched
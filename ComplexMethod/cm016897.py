def _run_scan(self) -> None:
        """Main scan loop running in background thread."""
        t_start = time.perf_counter()
        roots = self._roots
        phase = self._phase
        cancelled = False
        total_created = 0
        total_enriched = 0
        skipped_existing = 0
        total_paths = 0

        try:
            if not dependencies_available():
                self._add_error("Database dependencies not available")
                self._emit_event(
                    "assets.seed.error",
                    {"message": "Database dependencies not available"},
                )
                return

            if self._prune_first:
                all_prefixes = get_all_known_prefixes()
                marked = mark_missing_outside_prefixes_safely(all_prefixes)
                if marked > 0:
                    logging.info("Marked %d refs as missing before scan", marked)

            if self._check_pause_and_cancel():
                logging.info("Asset scan cancelled after pruning phase")
                cancelled = True
                return

            self._log_scan_config(roots)

            # Phase 1: Fast scan (stub records)
            if phase in (ScanPhase.FAST, ScanPhase.FULL):
                created, skipped, paths = self._run_fast_phase(roots)
                total_created, skipped_existing, total_paths = created, skipped, paths

                if self._check_pause_and_cancel():
                    cancelled = True
                    return

                self._emit_event(
                    "assets.seed.fast_complete",
                    {
                        "roots": list(roots),
                        "created": total_created,
                        "skipped": skipped_existing,
                        "total": total_paths,
                    },
                )

            # Phase 2: Enrichment scan (metadata + hashes)
            if phase in (ScanPhase.ENRICH, ScanPhase.FULL):
                if self._check_pause_and_cancel():
                    cancelled = True
                    return

                enrich_cancelled, total_enriched = self._run_enrich_phase(roots)

                if enrich_cancelled:
                    cancelled = True
                    return

                self._emit_event(
                    "assets.seed.enrich_complete",
                    {
                        "roots": list(roots),
                        "enriched": total_enriched,
                    },
                )

            elapsed = time.perf_counter() - t_start
            logging.info(
                "Scan(%s, %s) done %.3fs: created=%d enriched=%d skipped=%d",
                roots,
                phase.value,
                elapsed,
                total_created,
                total_enriched,
                skipped_existing,
            )

            self._emit_event(
                "assets.seed.completed",
                {
                    "phase": phase.value,
                    "total": total_paths,
                    "created": total_created,
                    "enriched": total_enriched,
                    "skipped": skipped_existing,
                    "elapsed": round(elapsed, 3),
                },
            )

        except Exception as e:
            self._add_error(f"Scan failed: {e}")
            logging.exception("Asset scan failed")
            self._emit_event("assets.seed.error", {"message": str(e)})
        finally:
            if cancelled:
                self._emit_event(
                    "assets.seed.cancelled",
                    {
                        "scanned": self._progress.scanned if self._progress else 0,
                        "total": total_paths,
                        "created": total_created,
                    },
                )
            with self._lock:
                self._reset_to_idle()
                pending = self._pending_enrich
                if pending is not None:
                    self._pending_enrich = None
                    if not self.start_enrich(
                        roots=pending["roots"],
                        compute_hashes=pending["compute_hashes"],
                    ):
                        logging.warning(
                            "Pending enrich scan could not start (roots=%s)",
                            pending["roots"],
                        )
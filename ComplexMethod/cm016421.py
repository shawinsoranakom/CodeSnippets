def test_concurrent_enqueue_during_drain_not_lost(
        self, fresh_seeder: _AssetSeeder,
    ):
        """A second enqueue_enrich arriving while drain is in progress is not lost.

        Because the drain now holds _lock through the start_enrich call,
        a concurrent enqueue_enrich will block until start_enrich has
        transitioned state to RUNNING, then the enqueue will queue its
        payload as _pending_enrich for the *next* drain.
        """
        scan_barrier = threading.Event()
        scan_reached = threading.Event()
        enrich_barrier = threading.Event()
        enrich_reached = threading.Event()

        collect_call = 0

        def gated_collect(*args):
            nonlocal collect_call
            collect_call += 1
            if collect_call == 1:
                # First call: the initial fast scan
                scan_reached.set()
                scan_barrier.wait(timeout=5.0)
            return []

        enrich_call = 0

        def gated_get_unenriched(*args, **kwargs):
            nonlocal enrich_call
            enrich_call += 1
            if enrich_call == 1:
                # First enrich batch: signal and block
                enrich_reached.set()
                enrich_barrier.wait(timeout=5.0)
            return []

        with (
            patch("app.assets.seeder.dependencies_available", return_value=True),
            patch("app.assets.seeder.sync_root_safely", return_value=set()),
            patch("app.assets.seeder.collect_paths_for_roots", side_effect=gated_collect),
            patch("app.assets.seeder.build_asset_specs", return_value=([], set(), 0)),
            patch("app.assets.seeder.insert_asset_specs", return_value=0),
            patch("app.assets.seeder.get_unenriched_assets_for_roots", side_effect=gated_get_unenriched),
            patch("app.assets.seeder.enrich_assets_batch", return_value=(0, 0)),
        ):
            # 1. Start fast scan
            fresh_seeder.start(roots=("models",), phase=ScanPhase.FAST)
            assert scan_reached.wait(timeout=2.0)

            # 2. Queue enrich while fast scan is running
            queued = fresh_seeder.enqueue_enrich(
                roots=("input",), compute_hashes=False
            )
            assert queued is False

            # 3. Let the fast scan finish — drain will start the enrich scan
            scan_barrier.set()

            # 4. Wait until the drained enrich scan is running
            assert enrich_reached.wait(timeout=5.0)

            # 5. Now enqueue another enrich while the drained scan is running
            queued2 = fresh_seeder.enqueue_enrich(
                roots=("output",), compute_hashes=True
            )
            assert queued2 is False  # should be queued, not started

            # Verify _pending_enrich was set (the second enqueue was captured)
            with fresh_seeder._lock:
                assert fresh_seeder._pending_enrich is not None
                assert "output" in fresh_seeder._pending_enrich["roots"]

            # Let the enrich scan finish
            enrich_barrier.set()

        deadline = time.monotonic() + 5.0
        while fresh_seeder.get_status().state != State.IDLE and time.monotonic() < deadline:
            time.sleep(0.05)
def test_invalidating_cache(self):
        """Test that st.caches are cleared when a dependency changes."""
        # Make sure there are no caches from other tests.
        caching._mem_caches.clear()

        # Run st_cache_script.
        runner = TestScriptRunner("st_cache_script.py")
        runner.request_rerun(RerunData())
        runner.start()
        runner.join()

        # The script has 5 cached functions, each of which writes out
        # some text.
        self._assert_text_deltas(
            runner,
            [
                "cached function called",
                "cached function called",
                "cached function called",
                "cached function called",
                "cached_depending_on_not_yet_defined called",
            ],
        )

        # Set _cached_pages to None manually (instead of using
        # source_util.invalidate_pages_cache) to avoid firing on_pages_changed
        # events.
        source_util._cached_pages = None

        # Run a slightly different script on a second runner.
        runner = TestScriptRunner("st_cache_script_changed.py")
        runner.request_rerun(RerunData())
        runner.start()
        runner.join()

        # The cached functions should not have been called on this second run,
        # except for the one that has actually changed.
        self._assert_text_deltas(
            runner,
            [
                "cached_depending_on_not_yet_defined called",
            ],
        )
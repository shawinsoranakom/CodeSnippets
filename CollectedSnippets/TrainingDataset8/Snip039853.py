def test_rerun_caching(self):
        """Test that st.caches are maintained across script runs."""
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

        # Re-run the script on a second runner.
        runner = TestScriptRunner("st_cache_script.py")
        runner.request_rerun(RerunData())
        runner.start()
        runner.join()

        # The cached functions should not have been called on this second run
        self._assert_text_deltas(runner, [])
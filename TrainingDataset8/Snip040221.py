def test_fix_matplotlib_crash(self):
        """Test that bootstrap.run sets the matplotlib backend to
        "Agg" if config.runner.fixMatplotlib=True.
        """
        # TODO: Find a proper way to mock sys.platform
        ORIG_PLATFORM = sys.platform

        for platform, do_fix in [("darwin", True), ("linux2", True)]:
            sys.platform = platform

            matplotlib.use("pdf", force=True)

            config._set_option("runner.fixMatplotlib", True, "test")
            bootstrap.run("/not/a/script", "", [], {})
            if do_fix:
                self.assertEqual("agg", matplotlib.get_backend().lower())
            else:
                self.assertEqual("pdf", matplotlib.get_backend().lower())

            # Reset
            matplotlib.use("pdf", force=True)

            config._set_option("runner.fixMatplotlib", False, "test")
            bootstrap.run("/not/a/script", "", [], {})
            self.assertEqual("pdf", matplotlib.get_backend().lower())

        sys.platform = ORIG_PLATFORM
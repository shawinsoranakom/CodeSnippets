def test_post_processing(self):
        """
        post_processing behaves correctly.

        Files that are alterable should always be post-processed; files that
        aren't should be skipped.

        collectstatic has already been called once in setUp() for this
        testcase, therefore we check by verifying behavior on a second run.
        """
        collectstatic_args = {
            "interactive": False,
            "verbosity": 0,
            "link": False,
            "clear": False,
            "dry_run": False,
            "post_process": True,
            "use_default_ignore_patterns": True,
            "ignore_patterns": ["*.ignoreme"],
        }

        collectstatic_cmd = CollectstaticCommand()
        collectstatic_cmd.set_options(**collectstatic_args)
        stats = collectstatic_cmd.collect()
        self.assertIn(
            os.path.join("cached", "css", "window.css"), stats["post_processed"]
        )
        self.assertIn(
            os.path.join("cached", "css", "img", "window.png"), stats["unmodified"]
        )
        self.assertIn(os.path.join("test", "nonascii.css"), stats["post_processed"])
        # No file should be yielded twice.
        self.assertCountEqual(stats["post_processed"], set(stats["post_processed"]))
        self.assertPostCondition()
def test_command_tracking_limits(self):
        """Command tracking limits should be respected.

        Current limits are 25 per unique command and 200 in total.
        """
        ctx = get_script_run_ctx()
        ctx.reset()
        ctx.gather_usage_stats = True

        funcs = []
        for i in range(10):

            def test_function() -> str:
                return "foo"

            funcs.append(
                metrics_util.gather_metrics(f"test_function_{i}", test_function)
            )

        for _ in range(metrics_util._MAX_TRACKED_PER_COMMAND + 1):
            for func in funcs:
                func()

        self.assertLessEqual(
            len(ctx.tracked_commands), metrics_util._MAX_TRACKED_COMMANDS
        )

        # Test that no individual command is tracked more than _MAX_TRACKED_PER_COMMAND
        command_counts = Counter(
            [command.name for command in ctx.tracked_commands]
        ).most_common()
        self.assertLessEqual(
            command_counts[0][1], metrics_util._MAX_TRACKED_PER_COMMAND
        )
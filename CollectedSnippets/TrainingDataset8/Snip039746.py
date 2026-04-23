def test_internal_api_commands(self, command: Callable, expected_name: str):
        """Some internal functions are also tracked and should use the correct name."""
        ctx = get_script_run_ctx()

        # This will always throw an exception because of missing arguments
        # This is fine since the command still get tracked
        with contextlib.suppress(Exception):
            command()

        self.assertGreater(
            len(ctx.tracked_commands),
            0,
            f"No command tracked for {expected_name}",
        )

        # Sometimes multiple commands are executed
        # so we check the full list of tracked commands
        self.assertIn(
            expected_name,
            [tracked_commands.name for tracked_commands in ctx.tracked_commands],
            f"Command {expected_name} was not tracked.",
        )
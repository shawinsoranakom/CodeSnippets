def test_public_api_commands(self):
        """All commands of the public API should be tracked with the correct name."""
        ctx = get_script_run_ctx()

        # Some commands are currently not tracked for various reasons:
        ignored_commands = {
            "experimental_rerun",
            "stop",
            "spinner",
            "empty",
            "progress",
            "get_option",
        }

        public_commands = {
            k
            for k, v in st.__dict__.items()
            if not k.startswith("_") and not isinstance(v, type(st))
        }

        for command_name in public_commands.difference(ignored_commands):
            if command_name in ignored_commands:
                continue
            command = getattr(st, command_name)
            if callable(command):
                # This will always throw an exception because of missing arguments
                # This is fine since the command still get tracked
                with contextlib.suppress(Exception):
                    command()

                self.assertGreater(
                    len(ctx.tracked_commands),
                    0,
                    f"No command tracked for {command_name}",
                )

                # Sometimes also multiple commands are executed
                # so we check the full list.
                self.assertIn(
                    command_name,
                    [
                        tracked_commands.name
                        for tracked_commands in ctx.tracked_commands
                    ],
                )

                ctx.reset()
                ctx.gather_usage_stats = True
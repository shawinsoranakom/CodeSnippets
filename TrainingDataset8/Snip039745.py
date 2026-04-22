def test_gather_metrics_decorator(self):
        """The gather_metrics decorator works as expected."""
        ctx = get_script_run_ctx()

        @metrics_util.gather_metrics("test_function")
        def test_function(param1: int, param2: str, param3: float = 0.1) -> str:
            st.markdown("This command should not be tracked")
            return "foo"

        test_function(param1=10, param2="foobar")

        self.assertEqual(len(ctx.tracked_commands), 1)
        self.assertTrue(ctx.tracked_commands[0].name.endswith("test_function"))
        self.assertTrue(ctx.tracked_commands[0].name.startswith("external:"))

        st.markdown("This function should be tracked")

        self.assertEqual(len(ctx.tracked_commands), 2)
        self.assertTrue(ctx.tracked_commands[0].name.endswith("test_function"))
        self.assertTrue(ctx.tracked_commands[0].name.startswith("external:"))
        self.assertEqual(ctx.tracked_commands[1].name, "markdown")

        ctx.reset()
        # Deactivate usage stats gathering
        ctx.gather_usage_stats = False

        self.assertEqual(len(ctx.tracked_commands), 0)
        test_function(param1=10, param2="foobar")
        self.assertEqual(len(ctx.tracked_commands), 0)
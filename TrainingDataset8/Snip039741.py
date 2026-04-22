def setUp(self):
        super().setUp()
        ctx = get_script_run_ctx()
        ctx.reset()
        ctx.gather_usage_stats = True
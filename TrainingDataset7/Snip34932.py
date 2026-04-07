def test_init_debug_mode(self):
        runner = DiscoverRunner()
        self.assertFalse(runner.debug_mode)
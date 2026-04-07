def test_add_arguments_debug_mode(self):
        parser = ArgumentParser()
        DiscoverRunner.add_arguments(parser)

        ns = parser.parse_args([])
        self.assertFalse(ns.debug_mode)
        ns = parser.parse_args(["--debug-mode"])
        self.assertTrue(ns.debug_mode)
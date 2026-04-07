def test_add_arguments_shuffle(self):
        parser = ArgumentParser()
        DiscoverRunner.add_arguments(parser)
        ns = parser.parse_args([])
        self.assertIs(ns.shuffle, False)
        ns = parser.parse_args(["--shuffle"])
        self.assertIsNone(ns.shuffle)
        ns = parser.parse_args(["--shuffle", "5"])
        self.assertEqual(ns.shuffle, 5)
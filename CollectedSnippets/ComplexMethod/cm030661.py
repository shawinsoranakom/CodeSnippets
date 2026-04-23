def test_collect(self):
        self.preclean()
        gc.collect()
        # Algorithmically verify the contents of self.visit
        # because it is long and tortuous.

        # Count the number of visits to each callback
        n = [v[0] for v in self.visit]
        n1 = [i for i in n if i == 1]
        n2 = [i for i in n if i == 2]
        self.assertEqual(n1, [1]*2)
        self.assertEqual(n2, [2]*2)

        # Count that we got the right number of start and stop callbacks.
        n = [v[1] for v in self.visit]
        n1 = [i for i in n if i == "start"]
        n2 = [i for i in n if i == "stop"]
        self.assertEqual(n1, ["start"]*2)
        self.assertEqual(n2, ["stop"]*2)

        # Check that we got the right info dict for all callbacks
        for v in self.visit:
            info = v[2]
            self.assertIn("generation", info)
            self.assertIn("collected", info)
            self.assertIn("uncollectable", info)
            self.assertIn("candidates", info)
            self.assertIn("duration", info)
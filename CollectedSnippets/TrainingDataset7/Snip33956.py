def test_resetcycle05(self):
        output = self.engine.render_to_string("resetcycle05", {"test": list(range(5))})
        self.assertEqual(output, "aaaaa")
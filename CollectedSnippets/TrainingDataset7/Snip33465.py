def test_cache08(self):
        """
        Allow first argument to be a variable.
        """
        context = {"foo": 2, "time": 2}
        self.engine.render_to_string("cache06", context)
        output = self.engine.render_to_string("cache08", context)
        self.assertEqual(output, "cache06")
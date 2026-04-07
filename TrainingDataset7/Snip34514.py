def test_no_wrapped_exception(self):
        """
        # 16770 -- The template system doesn't wrap exceptions, but annotates
        them.
        """
        engine = self._engine()
        c = Context({"coconuts": lambda: 42 / 0})
        t = engine.from_string("{{ coconuts }}")

        with self.assertRaises(ZeroDivisionError) as e:
            t.render(c)

        if self.debug_engine:
            debug = e.exception.template_debug
            self.assertEqual(debug["start"], 0)
            self.assertEqual(debug["end"], 14)
def test_chained_exception_forwarded(self):
        with self.assertRaises(TemplateDoesNotExist) as ctx:
            engine.get_template("not_there.html#not-a-partial")

        exception = ctx.exception
        self.assertGreater(len(exception.tried), 0)
        origin, _ = exception.tried[0]
        self.assertEqual(origin.template_name, "not_there.html")
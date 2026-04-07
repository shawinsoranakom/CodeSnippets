def test_include_template_argument(self):
        """
        Support any render() supporting object
        """
        engine = Engine()
        ctx = Context(
            {
                "tmpl": engine.from_string("This worked!"),
            }
        )
        outer_tmpl = engine.from_string("{% include tmpl %}")
        output = outer_tmpl.render(ctx)
        self.assertEqual(output, "This worked!")
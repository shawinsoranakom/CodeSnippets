def test_self_context(self):
        """
        Using 'self' in the context should not throw errors (#24538).
        """
        # self will be overridden to be a TemplateReference, so the self
        # variable will not come through. Attempting to use one though should
        # not throw an error.
        template = self.engine.from_string("hello {{ foo }}!")
        content = template.render(context={"self": "self", "foo": "world"})
        self.assertEqual(content, "hello world!")
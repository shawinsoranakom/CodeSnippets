def test_extend_self_error(self):
        """
        Catch if a template extends itself and no other matching
        templates are found.
        """
        engine = Engine(dirs=[os.path.join(RECURSIVE, "fs")])
        template = engine.get_template("self.html")
        with self.assertRaises(TemplateDoesNotExist) as e:
            template.render(Context({}))
        tried = e.exception.tried
        self.assertEqual(len(tried), 1)
        origin, message = tried[0]
        self.assertEqual(origin.template_name, "self.html")
        self.assertEqual(message, "Skipped to avoid recursion")
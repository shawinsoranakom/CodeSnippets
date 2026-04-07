def test_extend_missing(self):
        engine = Engine(dirs=[os.path.join(RECURSIVE, "fs")])
        template = engine.get_template("extend-missing.html")
        with self.assertRaises(TemplateDoesNotExist) as e:
            template.render(Context({}))

        tried = e.exception.tried
        self.assertEqual(len(tried), 1)
        self.assertEqual(tried[0][0].template_name, "missing.html")
def test_normal_extend(self):
        engine = Engine(dirs=[os.path.join(RECURSIVE, "fs")])
        template = engine.get_template("one.html")
        output = template.render(Context({}))
        self.assertEqual(output.strip(), "three two one")
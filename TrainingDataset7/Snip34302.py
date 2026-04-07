def test_normal_extend(self):
        engine = Engine(dirs=[RELATIVE])
        template = engine.get_template("one.html")
        output = template.render(Context({}))
        self.assertEqual(output.strip(), "three two one")
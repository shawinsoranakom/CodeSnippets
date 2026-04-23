def test_mixing1(self):
        engine = Engine(dirs=[RELATIVE])
        template = engine.get_template("dir1/two.html")
        output = template.render(Context({}))
        self.assertEqual(output.strip(), "three two one dir2 one dir1 two")
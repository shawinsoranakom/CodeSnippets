def test_mixing2(self):
        engine = Engine(dirs=[RELATIVE])
        template = engine.get_template("dir1/three.html")
        output = template.render(Context({}))
        self.assertEqual(output.strip(), "three dir1 three")
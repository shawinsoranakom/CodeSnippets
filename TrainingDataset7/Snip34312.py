def test_dir2_include(self):
        engine = Engine(dirs=[RELATIVE])
        template = engine.get_template("dir1/dir2/inc1.html")
        output = template.render(Context({}))
        self.assertEqual(output.strip(), "three")
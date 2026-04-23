def test_normal_include(self):
        engine = Engine(dirs=[RELATIVE])
        template = engine.get_template("dir1/dir2/inc2.html")
        output = template.render(Context({}))
        self.assertEqual(output.strip(), "dir2 include")
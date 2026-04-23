def test_dir2_extend(self):
        engine = Engine(dirs=[RELATIVE])
        template = engine.get_template("dir1/dir2/one.html")
        output = template.render(Context({}))
        self.assertEqual(output.strip(), "three two one dir2 one")
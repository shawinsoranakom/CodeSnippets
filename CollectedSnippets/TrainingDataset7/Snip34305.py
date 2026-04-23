def test_dir1_extend1(self):
        engine = Engine(dirs=[RELATIVE])
        template = engine.get_template("dir1/one1.html")
        output = template.render(Context({}))
        self.assertEqual(output.strip(), "three two one dir1 one")
def test_dir1_extend3(self):
        engine = Engine(dirs=[RELATIVE])
        template = engine.get_template("dir1/one3.html")
        output = template.render(Context({}))
        self.assertEqual(output.strip(), "three two one dir1 one")
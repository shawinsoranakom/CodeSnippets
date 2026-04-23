def test_normal_include_variable(self):
        engine = Engine(dirs=[RELATIVE])
        template = engine.get_template("dir1/dir2/inc3.html")
        output = template.render(Context({"tmpl": "./include_content.html"}))
        self.assertEqual(output.strip(), "dir2 include")
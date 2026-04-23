def test_normal_extend_variable(self):
        engine = Engine(dirs=[RELATIVE])
        template = engine.get_template("one_var.html")
        output = template.render(Context({"tmpl": "./two.html"}))
        self.assertEqual(output.strip(), "three two one")
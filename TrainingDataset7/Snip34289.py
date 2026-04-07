def test_origin(self):
        engine = Engine(dirs=[TEMPLATE_DIR], debug=True)
        template = engine.get_template("index.html")
        self.assertEqual(template.origin.template_name, "index.html")
def test_include_from_loader_get_template(self):
        tmpl = loader.get_template("include_tpl.html")  # {% include tmpl %}
        output = tmpl.render({"tmpl": loader.get_template("index.html")})
        self.assertEqual(output, "index\n\n")
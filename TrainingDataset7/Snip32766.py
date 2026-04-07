def test_no_directory_traversal(self):
        with self.assertRaises(TemplateDoesNotExist):
            self.engine.get_template("../forbidden/template_backends/hello.html")
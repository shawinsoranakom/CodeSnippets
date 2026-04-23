def test_bad_404_template(self):
        "Errors found when rendering 404 error templates are re-raised"
        with self.assertRaises(TemplateSyntaxError):
            self.client.get("/no_such_view/")
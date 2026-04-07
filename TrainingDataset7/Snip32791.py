def test_select_template_not_found(self):
        with self.assertRaises(TemplateDoesNotExist) as e:
            select_template(
                ["template_loader/unknown.html", "template_loader/missing.html"]
            )
        self.assertEqual(
            e.exception.chain[0].tried[0][0].template_name,
            "template_loader/unknown.html",
        )
        self.assertEqual(e.exception.chain[0].backend.name, "dummy")
        self.assertEqual(
            e.exception.chain[-1].tried[0][0].template_name,
            "template_loader/missing.html",
        )
        self.assertEqual(e.exception.chain[-1].backend.name, "django")
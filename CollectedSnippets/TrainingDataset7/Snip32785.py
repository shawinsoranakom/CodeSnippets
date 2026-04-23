def test_get_template_not_found(self):
        with self.assertRaises(TemplateDoesNotExist) as e:
            get_template("template_loader/unknown.html")
        self.assertEqual(
            e.exception.chain[-1].tried[0][0].template_name,
            "template_loader/unknown.html",
        )
        self.assertEqual(e.exception.chain[-1].backend.name, "django")
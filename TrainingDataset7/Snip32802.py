def test_render_to_string_with_list_not_found(self):
        with self.assertRaises(TemplateDoesNotExist) as e:
            render_to_string(
                ["template_loader/unknown.html", "template_loader/missing.html"]
            )
        self.assertEqual(
            e.exception.chain[0].tried[0][0].template_name,
            "template_loader/unknown.html",
        )
        self.assertEqual(e.exception.chain[0].backend.name, "dummy")
        self.assertEqual(
            e.exception.chain[1].tried[0][0].template_name,
            "template_loader/unknown.html",
        )
        self.assertEqual(e.exception.chain[1].backend.name, "django")
        self.assertEqual(
            e.exception.chain[2].tried[0][0].template_name,
            "template_loader/missing.html",
        )
        self.assertEqual(e.exception.chain[2].backend.name, "dummy")
        self.assertEqual(
            e.exception.chain[3].tried[0][0].template_name,
            "template_loader/missing.html",
        )
        self.assertEqual(e.exception.chain[3].backend.name, "django")
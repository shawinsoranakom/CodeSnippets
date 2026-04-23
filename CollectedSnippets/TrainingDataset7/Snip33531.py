def test_unknown_origin_relative_path(self):
        files = ["./nonexistent.html", "../nonexistent.html"]
        for template_name in files:
            with self.subTest(template_name=template_name):
                msg = (
                    f"The relative path '{template_name}' cannot be evaluated due to "
                    "an unknown template origin."
                )
                with self.assertRaisesMessage(TemplateSyntaxError, msg):
                    Template(f"{{% extends '{template_name}' %}}")
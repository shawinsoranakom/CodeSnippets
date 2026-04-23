def test_invalid_template_name_raises_template_does_not_exist(self):
        for template_name in [123, None, "", "#", "#name"]:
            with (
                self.subTest(template_name=template_name),
                self.assertRaisesMessage(TemplateDoesNotExist, str(template_name)),
            ):
                engine.get_template(template_name)
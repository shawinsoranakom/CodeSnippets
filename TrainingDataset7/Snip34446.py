def test_template_extract_extra_data_robust(self):
        partial_name = "some_partial_name"
        for extra_data in (
            None,
            0,
            [],
            {},
            {"wrong-key": {}},
            {"partials": None},
            {"partials": {}},
            {"partials": []},
            {"partials": 0},
        ):
            with (
                self.subTest(extra_data=extra_data),
                self.override_get_template(extra_data=extra_data),
                self.assertRaisesMessage(TemplateDoesNotExist, partial_name),
            ):
                engine.get_template(f"template.html#{partial_name}")
def test_boundfield_label_tag(self):
        class SomeForm(Form):
            field = CharField()

        boundfield = SomeForm()["field"]

        testcases = [  # (args, kwargs, expected_label, expected_legend)
            # without anything: just print the <label>/<legend>
            ((), {}, '<label for="id_field">Field:</label>', "<legend>Field:</legend>"),
            # passing just one argument: overrides the field's label
            (
                ("custom",),
                {},
                '<label for="id_field">custom:</label>',
                "<legend>custom:</legend>",
            ),
            # the overridden label is escaped
            (
                ("custom&",),
                {},
                '<label for="id_field">custom&amp;:</label>',
                "<legend>custom&amp;:</legend>",
            ),
            (
                (mark_safe("custom&"),),
                {},
                '<label for="id_field">custom&:</label>',
                "<legend>custom&:</legend>",
            ),
            # Passing attrs to add extra attributes on the <label>/<legend>
            (
                (),
                {"attrs": {"class": "pretty"}},
                '<label for="id_field" class="pretty">Field:</label>',
                '<legend class="pretty">Field:</legend>',
            ),
        ]

        for args, kwargs, expected_label, expected_legend in testcases:
            with self.subTest(args=args, kwargs=kwargs):
                self.assertHTMLEqual(
                    boundfield.label_tag(*args, **kwargs),
                    expected_label,
                )
                self.assertHTMLEqual(
                    boundfield.legend_tag(*args, **kwargs),
                    expected_legend,
                )
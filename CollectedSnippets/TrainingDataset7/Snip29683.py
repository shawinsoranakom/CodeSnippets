def test_checkbox_get_context_attrs(self):
        context = SplitArrayWidget(
            forms.CheckboxInput(),
            size=2,
        ).get_context("name", [True, False])
        self.assertEqual(context["widget"]["value"], "[True, False]")
        self.assertEqual(
            [subwidget["attrs"] for subwidget in context["widget"]["subwidgets"]],
            [{"checked": True}, {}],
        )
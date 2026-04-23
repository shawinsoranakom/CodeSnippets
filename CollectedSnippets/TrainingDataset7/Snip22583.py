def test_floatfield_widget_attrs(self):
        f = FloatField(widget=NumberInput(attrs={"step": 0.01, "max": 1.0, "min": 0.0}))
        self.assertWidgetRendersTo(
            f,
            '<input step="0.01" name="f" min="0.0" max="1.0" type="number" id="id_f" '
            "required>",
        )
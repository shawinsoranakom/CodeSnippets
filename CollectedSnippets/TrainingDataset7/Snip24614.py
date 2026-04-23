def test_pointfield(self):
        class PointForm(forms.Form):
            p = forms.PointField()

        geom = self.geometries["point"]
        form = PointForm(data={"p": geom})
        self.assertTextarea(geom, form.as_p())
        self.assertMapWidget(form, "Point")
        self.assertFalse(PointForm().is_valid())
        invalid = PointForm(data={"p": "some invalid geom"})
        self.assertFalse(invalid.is_valid())
        self.assertIn("Invalid geometry value", str(invalid.errors))

        for invalid in [geo for key, geo in self.geometries.items() if key != "point"]:
            self.assertFalse(PointForm(data={"p": invalid.wkt}).is_valid())
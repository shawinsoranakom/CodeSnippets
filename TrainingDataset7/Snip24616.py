def test_linestringfield(self):
        class LineStringForm(forms.Form):
            f = forms.LineStringField()

        geom = self.geometries["linestring"]
        form = LineStringForm(data={"f": geom})
        self.assertTextarea(geom, form.as_p())
        self.assertMapWidget(form, "LineString")
        self.assertFalse(LineStringForm().is_valid())

        for invalid in [
            geo for key, geo in self.geometries.items() if key != "linestring"
        ]:
            self.assertFalse(LineStringForm(data={"p": invalid.wkt}).is_valid())
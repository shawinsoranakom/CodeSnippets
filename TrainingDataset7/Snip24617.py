def test_multilinestringfield(self):
        class LineStringForm(forms.Form):
            f = forms.MultiLineStringField()

        geom = self.geometries["multilinestring"]
        form = LineStringForm(data={"f": geom})
        self.assertTextarea(geom, form.as_p())
        self.assertMapWidget(form, "MultiLineString")
        self.assertFalse(LineStringForm().is_valid())

        for invalid in [
            geo for key, geo in self.geometries.items() if key != "multilinestring"
        ]:
            self.assertFalse(LineStringForm(data={"p": invalid.wkt}).is_valid())
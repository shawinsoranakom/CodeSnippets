def test_multipointfield(self):
        class PointForm(forms.Form):
            p = forms.MultiPointField()

        geom = self.geometries["multipoint"]
        form = PointForm(data={"p": geom})
        self.assertTextarea(geom, form.as_p())
        self.assertMapWidget(form, "MultiPoint")
        self.assertFalse(PointForm().is_valid())

        for invalid in [
            geo for key, geo in self.geometries.items() if key != "multipoint"
        ]:
            self.assertFalse(PointForm(data={"p": invalid.wkt}).is_valid())
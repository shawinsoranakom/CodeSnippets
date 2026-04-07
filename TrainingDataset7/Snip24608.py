def test_field_with_text_widget(self):
        class PointForm(forms.Form):
            pt = forms.PointField(srid=4326, widget=forms.TextInput)

        form = PointForm()
        cleaned_pt = form.fields["pt"].clean("POINT(5 23)")
        self.assertEqual(cleaned_pt, GEOSGeometry("POINT(5 23)", srid=4326))
        self.assertEqual(4326, cleaned_pt.srid)
        with self.assertRaisesMessage(ValidationError, "Invalid geometry value."):
            form.fields["pt"].clean("POINT(5)")

        point = GEOSGeometry("SRID=4326;POINT(5 23)")
        form = PointForm(data={"pt": "POINT(5 23)"}, initial={"pt": point})
        self.assertFalse(form.has_changed())
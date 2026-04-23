def test_build_attrs_not_required_field(self):
        form = NotRequiredBandForm()
        attrs = form["band"].field.widget.build_attrs({})
        self.assertJSONEqual(attrs["data-allow-clear"], True)
def test_build_attrs_required_field(self):
        form = RequiredBandForm()
        attrs = form["band"].field.widget.build_attrs({})
        self.assertJSONEqual(attrs["data-allow-clear"], False)
def test_build_attrs_no_custom_class(self):
        form = AlbumForm()
        attrs = form["featuring"].field.widget.get_context(
            name="name", value=None, attrs={}
        )["widget"]["attrs"]
        self.assertEqual(attrs["class"], "admin-autocomplete")
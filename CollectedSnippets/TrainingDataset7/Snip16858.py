def test_render_unsafe_limit_choices_to(self):
        rel = UnsafeLimitChoicesTo._meta.get_field("band").remote_field
        w = widgets.ForeignKeyRawIdWidget(rel, widget_admin_site)
        self.assertHTMLEqual(
            w.render("test", None),
            '<div><input type="text" name="test" class="vForeignKeyRawIdAdminField">'
            '<a href="/admin_widgets/band/?name=%22%26%3E%3Cescapeme&amp;'
            '_to_field=artist_ptr" class="related-lookup" id="lookup_id_test" '
            'title="Lookup"></a></div>',
        )
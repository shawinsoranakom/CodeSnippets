def test_render_fk_as_pk_model(self):
        rel = VideoStream._meta.get_field("release_event").remote_field
        w = widgets.ForeignKeyRawIdWidget(rel, widget_admin_site)
        self.assertHTMLEqual(
            w.render("test", None),
            '<div><input type="text" name="test" class="vForeignKeyRawIdAdminField">'
            '<a href="/admin_widgets/releaseevent/?_to_field=album" '
            'class="related-lookup" id="lookup_id_test" title="Lookup"></a></div>',
        )
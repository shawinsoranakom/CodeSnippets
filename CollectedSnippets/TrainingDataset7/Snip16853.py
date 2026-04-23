def test_render(self):
        band = Band.objects.create(name="Linkin Park")
        band.album_set.create(
            name="Hybrid Theory", cover_art=r"albums\hybrid_theory.jpg"
        )
        rel_uuid = Album._meta.get_field("band").remote_field
        w = widgets.ForeignKeyRawIdWidget(rel_uuid, widget_admin_site)
        self.assertHTMLEqual(
            w.render("test", band.uuid, attrs={}),
            '<div><input type="text" name="test" value="%(banduuid)s" '
            'class="vForeignKeyRawIdAdminField vUUIDField">'
            '<a href="/admin_widgets/band/?_to_field=uuid" class="related-lookup" '
            'id="lookup_id_test" title="Lookup"></a>&nbsp;<strong>'
            '<a href="/admin_widgets/band/%(bandpk)s/change/">Linkin Park</a>'
            "</strong></div>" % {"banduuid": band.uuid, "bandpk": band.pk},
        )

        rel_id = ReleaseEvent._meta.get_field("album").remote_field
        w = widgets.ForeignKeyRawIdWidget(rel_id, widget_admin_site)
        self.assertHTMLEqual(
            w.render("test", None, attrs={}),
            '<div><input type="text" name="test" class="vForeignKeyRawIdAdminField">'
            '<a href="/admin_widgets/album/?_to_field=id" class="related-lookup" '
            'id="lookup_id_test" title="Lookup"></a></div>',
        )
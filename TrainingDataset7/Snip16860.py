def test_render(self):
        band = Band.objects.create(name="Linkin Park")

        m1 = Member.objects.create(name="Chester")
        m2 = Member.objects.create(name="Mike")
        band.members.add(m1, m2)
        rel = Band._meta.get_field("members").remote_field

        w = widgets.ManyToManyRawIdWidget(rel, widget_admin_site)
        self.assertHTMLEqual(
            w.render("test", [m1.pk, m2.pk], attrs={}),
            (
                '<div><input type="text" name="test" value="%(m1pk)s,%(m2pk)s" '
                '   class="vManyToManyRawIdAdminField">'
                '<a href="/admin_widgets/member/" class="related-lookup" '
                '   id="lookup_id_test" title="Lookup"></a></div>'
            )
            % {"m1pk": m1.pk, "m2pk": m2.pk},
        )

        self.assertHTMLEqual(
            w.render("test", [m1.pk]),
            (
                '<div><input type="text" name="test" value="%(m1pk)s" '
                '   class="vManyToManyRawIdAdminField">'
                '<a href="/admin_widgets/member/" class="related-lookup" '
                '   id="lookup_id_test" title="Lookup"></a></div>'
            )
            % {"m1pk": m1.pk},
        )
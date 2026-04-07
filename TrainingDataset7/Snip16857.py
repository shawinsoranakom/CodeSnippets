def test_proper_manager_for_label_lookup(self):
        # see #9258
        rel = Inventory._meta.get_field("parent").remote_field
        w = widgets.ForeignKeyRawIdWidget(rel, widget_admin_site)

        hidden = Inventory.objects.create(barcode=93, name="Hidden", hidden=True)
        child_of_hidden = Inventory.objects.create(
            barcode=94, name="Child of hidden", parent=hidden
        )
        self.assertHTMLEqual(
            w.render("test", child_of_hidden.parent_id, attrs={}),
            '<div><input type="text" name="test" value="93" '
            '   class="vForeignKeyRawIdAdminField">'
            '<a href="/admin_widgets/inventory/?_to_field=barcode" '
            'class="related-lookup" id="lookup_id_test" title="Lookup"></a>'
            '&nbsp;<strong><a href="/admin_widgets/inventory/%(pk)s/change/">'
            "Hidden</a></strong></div>" % {"pk": hidden.pk},
        )
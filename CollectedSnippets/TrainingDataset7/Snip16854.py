def test_relations_to_non_primary_key(self):
        # ForeignKeyRawIdWidget works with fields which aren't related to
        # the model's primary key.
        apple = Inventory.objects.create(barcode=86, name="Apple")
        Inventory.objects.create(barcode=22, name="Pear")
        core = Inventory.objects.create(barcode=87, name="Core", parent=apple)
        rel = Inventory._meta.get_field("parent").remote_field
        w = widgets.ForeignKeyRawIdWidget(rel, widget_admin_site)
        self.assertHTMLEqual(
            w.render("test", core.parent_id, attrs={}),
            '<div><input type="text" name="test" value="86" '
            'class="vForeignKeyRawIdAdminField">'
            '<a href="/admin_widgets/inventory/?_to_field=barcode" '
            'class="related-lookup" id="lookup_id_test" title="Lookup"></a>'
            '&nbsp;<strong><a href="/admin_widgets/inventory/%(pk)s/change/">'
            "Apple</a></strong></div>" % {"pk": apple.pk},
        )
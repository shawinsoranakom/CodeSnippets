def test_radio_fields_foreignkey_formfield_overrides_empty_label(self):
        class MyModelAdmin(admin.ModelAdmin):
            radio_fields = {"parent": admin.VERTICAL}
            formfield_overrides = {
                ForeignKey: {"empty_label": "Custom empty label"},
            }

        ma = MyModelAdmin(Inventory, admin.site)
        ff = ma.formfield_for_dbfield(Inventory._meta.get_field("parent"), request=None)
        self.assertEqual(ff.empty_label, "Custom empty label")
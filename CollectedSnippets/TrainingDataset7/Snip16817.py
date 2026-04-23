def test_formfield_overrides_widget_instances(self):
        """
        Widget instances in formfield_overrides are not shared between
        different fields. (#19423)
        """

        class BandAdmin(admin.ModelAdmin):
            formfield_overrides = {
                CharField: {"widget": forms.TextInput(attrs={"size": "10"})}
            }

        ma = BandAdmin(Band, admin.site)
        f1 = ma.formfield_for_dbfield(Band._meta.get_field("name"), request=None)
        f2 = ma.formfield_for_dbfield(Band._meta.get_field("style"), request=None)
        self.assertNotEqual(f1.widget, f2.widget)
        self.assertEqual(f1.widget.attrs["maxlength"], "100")
        self.assertEqual(f2.widget.attrs["maxlength"], "20")
        self.assertEqual(f2.widget.attrs["size"], "10")
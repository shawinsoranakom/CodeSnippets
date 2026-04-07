def test_formfield_overrides_for_datetime_field(self):
        """
        Overriding the widget for DateTimeField doesn't overrides the default
        form_class for that field (#26449).
        """

        class MemberAdmin(admin.ModelAdmin):
            formfield_overrides = {
                DateTimeField: {"widget": widgets.AdminSplitDateTime}
            }

        ma = MemberAdmin(Member, admin.site)
        f1 = ma.formfield_for_dbfield(Member._meta.get_field("birthdate"), request=None)
        self.assertIsInstance(f1.widget, widgets.AdminSplitDateTime)
        self.assertIsInstance(f1, forms.SplitDateTimeField)
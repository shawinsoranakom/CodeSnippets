def test_get_fieldsets(self):
        # get_fieldsets is called when figuring out form fields.
        # Refs #18681.
        class MediaForm(ModelForm):
            class Meta:
                model = Media
                fields = "__all__"

        class MediaInline(GenericTabularInline):
            form = MediaForm
            model = Media
            can_delete = False

            def get_fieldsets(self, request, obj=None):
                return [(None, {"fields": ["url", "description"]})]

        ma = MediaInline(Media, self.site)
        form = ma.get_formset(None).form
        self.assertEqual(form._meta.fields, ["url", "description"])
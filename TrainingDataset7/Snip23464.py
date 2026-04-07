def test_custom_form_meta_exclude_with_readonly(self):
        """
        The custom ModelForm's `Meta.exclude` is respected when
        used in conjunction with `GenericInlineModelAdmin.readonly_fields`
        and when no `ModelAdmin.exclude` is defined.
        """

        class MediaForm(ModelForm):
            class Meta:
                model = Media
                exclude = ["url"]

        class MediaInline(GenericTabularInline):
            readonly_fields = ["description"]
            form = MediaForm
            model = Media

        class EpisodeAdmin(admin.ModelAdmin):
            inlines = [MediaInline]

        ma = EpisodeAdmin(Episode, self.site)
        self.assertEqual(
            list(list(ma.get_formsets_with_inlines(request))[0][0]().forms[0].fields),
            ["keywords", "id", "DELETE"],
        )
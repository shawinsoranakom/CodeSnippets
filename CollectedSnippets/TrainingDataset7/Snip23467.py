def test_get_formsets_with_inlines_returns_tuples(self):
        """
        get_formsets_with_inlines() returns the correct tuples.
        """

        class MediaForm(ModelForm):
            class Meta:
                model = Media
                exclude = ["url"]

        class MediaInline(GenericTabularInline):
            form = MediaForm
            model = Media

        class AlternateInline(GenericTabularInline):
            form = MediaForm
            model = Media

        class EpisodeAdmin(admin.ModelAdmin):
            inlines = [AlternateInline, MediaInline]

        ma = EpisodeAdmin(Episode, self.site)
        inlines = ma.get_inline_instances(request)
        for (formset, inline), other_inline in zip(
            ma.get_formsets_with_inlines(request), inlines
        ):
            self.assertIsInstance(formset, other_inline.get_formset(request).__class__)
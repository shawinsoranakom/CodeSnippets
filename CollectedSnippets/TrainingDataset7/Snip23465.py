def test_custom_form_meta_exclude(self):
        """
        The custom ModelForm's `Meta.exclude` is respected by
        `GenericInlineModelAdmin.get_formset`, and overridden if
        `ModelAdmin.exclude` or `GenericInlineModelAdmin.exclude` are defined.
        Refs #15907.
        """
        # First with `GenericInlineModelAdmin`  -----------------

        class MediaForm(ModelForm):
            class Meta:
                model = Media
                exclude = ["url"]

        class MediaInline(GenericTabularInline):
            exclude = ["description"]
            form = MediaForm
            model = Media

        class EpisodeAdmin(admin.ModelAdmin):
            inlines = [MediaInline]

        ma = EpisodeAdmin(Episode, self.site)
        self.assertEqual(
            list(list(ma.get_formsets_with_inlines(request))[0][0]().forms[0].fields),
            ["url", "keywords", "id", "DELETE"],
        )

        # Then, only with `ModelForm`  -----------------

        class MediaInline(GenericTabularInline):
            form = MediaForm
            model = Media

        class EpisodeAdmin(admin.ModelAdmin):
            inlines = [MediaInline]

        ma = EpisodeAdmin(Episode, self.site)
        self.assertEqual(
            list(list(ma.get_formsets_with_inlines(request))[0][0]().forms[0].fields),
            ["description", "keywords", "id", "DELETE"],
        )
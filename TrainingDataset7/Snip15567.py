def test_verbose_name_plural_inline(self):
        class NonVerboseProfileInline(TabularInline):
            model = Profile
            verbose_name_plural = "Non-verbose childs"

        class VerboseNameProfileInline(TabularInline):
            model = VerboseNameProfile
            verbose_name_plural = "Childs with verbose name"

        class VerboseNamePluralProfileInline(TabularInline):
            model = VerboseNamePluralProfile
            verbose_name_plural = "Childs with verbose name plural"

        class BothVerboseNameProfileInline(TabularInline):
            model = BothVerboseNameProfile
            verbose_name_plural = "Childs with both verbose names"

        modeladmin = ModelAdmin(ProfileCollection, admin_site)
        modeladmin.inlines = [
            NonVerboseProfileInline,
            VerboseNameProfileInline,
            VerboseNamePluralProfileInline,
            BothVerboseNameProfileInline,
        ]
        obj = ProfileCollection.objects.create()
        url = reverse("admin:admin_inlines_profilecollection_change", args=(obj.pk,))
        request = self.factory.get(url)
        request.user = self.superuser
        response = modeladmin.changeform_view(request)
        # Non-verbose model.
        self.assertContains(
            response,
            (
                '<h2 id="profile_set-heading" class="inline-heading">'
                "Non-verbose childs</h2>"
            ),
            html=True,
        )
        self.assertContains(response, "Add another Profile")
        self.assertNotContains(
            response,
            '<h2 id="profile_set-heading" class="inline-heading">Profiles</h2>',
            html=True,
        )
        # Model with verbose name.
        self.assertContains(
            response,
            (
                '<h2 id="verbosenameprofile_set-heading" class="inline-heading">'
                "Childs with verbose name</h2>"
            ),
            html=True,
        )
        self.assertContains(response, "Add another Model with verbose name only")
        self.assertNotContains(
            response,
            '<h2 id="verbosenameprofile_set-heading" class="inline-heading">'
            "Model with verbose name onlys</h2>",
            html=True,
        )
        # Model with verbose name plural.
        self.assertContains(
            response,
            (
                '<h2 id="verbosenamepluralprofile_set-heading" class="inline-heading">'
                "Childs with verbose name plural</h2>"
            ),
            html=True,
        )
        self.assertContains(response, "Add another Profile")
        self.assertNotContains(
            response,
            '<h2 id="verbosenamepluralprofile_set-heading" class="inline-heading">'
            "Model with verbose name plural only</h2>",
            html=True,
        )
        # Model with both verbose names.
        self.assertContains(
            response,
            (
                '<h2 id="bothverbosenameprofile_set-heading" class="inline-heading">'
                "Childs with both verbose names</h2>"
            ),
            html=True,
        )
        self.assertContains(response, "Add another Model with both - name")
        self.assertNotContains(
            response,
            '<h2 id="bothverbosenameprofile_set-heading" class="inline-heading">'
            "Model with both - plural name</h2>",
            html=True,
        )
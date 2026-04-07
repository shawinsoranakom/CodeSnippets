def test_both_verbose_names_inline(self):
        class NonVerboseProfileInline(TabularInline):
            model = Profile
            verbose_name = "Non-verbose childs - name"
            verbose_name_plural = "Non-verbose childs - plural name"

        class VerboseNameProfileInline(TabularInline):
            model = VerboseNameProfile
            verbose_name = "Childs with verbose name - name"
            verbose_name_plural = "Childs with verbose name - plural name"

        class VerboseNamePluralProfileInline(TabularInline):
            model = VerboseNamePluralProfile
            verbose_name = "Childs with verbose name plural - name"
            verbose_name_plural = "Childs with verbose name plural - plural name"

        class BothVerboseNameProfileInline(TabularInline):
            model = BothVerboseNameProfile
            verbose_name = "Childs with both - name"
            verbose_name_plural = "Childs with both - plural name"

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
        self.assertNotContains(response, "Add another Profile")
        # Non-verbose model.
        self.assertContains(
            response,
            (
                '<h2 id="profile_set-heading" class="inline-heading">'
                "Non-verbose childs - plural name</h2>"
            ),
            html=True,
        )
        self.assertContains(response, "Add another Non-verbose childs - name")
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
                "Childs with verbose name - plural name</h2>"
            ),
            html=True,
        )
        self.assertContains(response, "Add another Childs with verbose name - name")
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
                "Childs with verbose name plural - plural name</h2>"
            ),
            html=True,
        )
        self.assertContains(
            response,
            "Add another Childs with verbose name plural - name",
        )
        self.assertNotContains(
            response,
            '<h2 id="verbosenamepluralprofile_set-heading" class="inline-heading">'
            "Model with verbose name plural only</h2>",
            html=True,
        )
        # Model with both verbose names.
        self.assertContains(
            response,
            '<h2 id="bothverbosenameprofile_set-heading" class="inline-heading">'
            "Childs with both - plural name</h2>",
            html=True,
        )
        self.assertContains(response, "Add another Childs with both - name")
        self.assertNotContains(
            response,
            '<h2 id="bothverbosenameprofile_set-heading" class="inline-heading">'
            "Model with both - plural name</h2>",
            html=True,
        )
        self.assertNotContains(response, "Add another Model with both - name")
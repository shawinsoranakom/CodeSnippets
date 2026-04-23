def test_change_list_sorting_model_meta(self):
        # Test ordering on Model Meta is respected

        l1 = Language.objects.create(iso="ur", name="Urdu")
        l2 = Language.objects.create(iso="ar", name="Arabic")
        link1 = reverse("admin:admin_views_language_change", args=(quote(l1.pk),))
        link2 = reverse("admin:admin_views_language_change", args=(quote(l2.pk),))

        response = self.client.get(reverse("admin:admin_views_language_changelist"), {})
        self.assertContentBefore(response, link2, link1)

        # Test we can override with query string
        response = self.client.get(
            reverse("admin:admin_views_language_changelist"), {"o": "-1"}
        )
        self.assertContentBefore(response, link1, link2)
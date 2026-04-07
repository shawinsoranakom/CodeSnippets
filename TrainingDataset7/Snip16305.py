def test_change_list_sorting_preserve_queryset_ordering(self):
        """
        If no ordering is defined in `ModelAdmin.ordering` or in the query
        string, then the underlying order of the queryset should not be
        changed, even if it is defined in `Modeladmin.get_queryset()`.
        Refs #11868, #7309.
        """
        p1 = Person.objects.create(name="Amy", gender=1, alive=True, age=80)
        p2 = Person.objects.create(name="Bob", gender=1, alive=True, age=70)
        p3 = Person.objects.create(name="Chris", gender=2, alive=False, age=60)
        link1 = reverse("admin:admin_views_person_change", args=(p1.pk,))
        link2 = reverse("admin:admin_views_person_change", args=(p2.pk,))
        link3 = reverse("admin:admin_views_person_change", args=(p3.pk,))

        response = self.client.get(reverse("admin:admin_views_person_changelist"), {})
        self.assertContentBefore(response, link3, link2)
        self.assertContentBefore(response, link2, link1)
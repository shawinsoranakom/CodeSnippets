def test_change_list_sorting_multiple(self):
        p1 = Person.objects.create(name="Chris", gender=1, alive=True)
        p2 = Person.objects.create(name="Chris", gender=2, alive=True)
        p3 = Person.objects.create(name="Bob", gender=1, alive=True)
        link1 = reverse("admin:admin_views_person_change", args=(p1.pk,))
        link2 = reverse("admin:admin_views_person_change", args=(p2.pk,))
        link3 = reverse("admin:admin_views_person_change", args=(p3.pk,))

        # Sort by name, gender
        response = self.client.get(
            reverse("admin:admin_views_person_changelist"), {"o": "1.2"}
        )
        self.assertContentBefore(response, link3, link1)
        self.assertContentBefore(response, link1, link2)

        # Sort by gender descending, name
        response = self.client.get(
            reverse("admin:admin_views_person_changelist"), {"o": "-2.1"}
        )
        self.assertContentBefore(response, link2, link3)
        self.assertContentBefore(response, link3, link1)
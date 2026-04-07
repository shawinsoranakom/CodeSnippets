def test_should_be_able_to_edit_related_objects_on_add_view(self):
        post = {
            "child_set-TOTAL_FORMS": "3",
            "child_set-INITIAL_FORMS": "0",
            "name": "Josh Stone",
            "child_set-0-name": "Paul",
            "child_set-1-name": "Catherine",
        }
        self.client.post(reverse("admin:admin_views_parent_add"), post)
        self.assertEqual(1, Parent.objects.count())
        self.assertEqual(2, Child.objects.count())

        children_names = list(
            Child.objects.order_by("name").values_list("name", flat=True)
        )

        self.assertEqual("Josh Stone", Parent.objects.latest("id").name)
        self.assertEqual(["Catherine Stone", "Paul Stone"], children_names)
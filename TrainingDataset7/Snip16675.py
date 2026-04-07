def test_should_be_able_to_edit_related_objects_on_change_view(self):
        parent = Parent.objects.create(name="Josh Stone")
        paul = Child.objects.create(parent=parent, name="Paul")
        catherine = Child.objects.create(parent=parent, name="Catherine")
        post = {
            "child_set-TOTAL_FORMS": "5",
            "child_set-INITIAL_FORMS": "2",
            "name": "Josh Stone",
            "child_set-0-name": "Paul",
            "child_set-0-id": paul.id,
            "child_set-1-name": "Catherine",
            "child_set-1-id": catherine.id,
        }
        self.client.post(
            reverse("admin:admin_views_parent_change", args=(parent.id,)), post
        )

        children_names = list(
            Child.objects.order_by("name").values_list("name", flat=True)
        )

        self.assertEqual("Josh Stone", Parent.objects.latest("id").name)
        self.assertEqual(["Catherine Stone", "Paul Stone"], children_names)
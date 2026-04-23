def test_should_be_able_to_edit_related_objects_on_changelist_view(self):
        parent = Parent.objects.create(name="Josh Rock")
        Child.objects.create(parent=parent, name="Paul")
        Child.objects.create(parent=parent, name="Catherine")
        post = {
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "1",
            "form-MAX_NUM_FORMS": "0",
            "form-0-id": parent.id,
            "form-0-name": "Josh Stone",
            "_save": "Save",
        }

        self.client.post(reverse("admin:admin_views_parent_changelist"), post)
        children_names = list(
            Child.objects.order_by("name").values_list("name", flat=True)
        )

        self.assertEqual("Josh Stone", Parent.objects.latest("id").name)
        self.assertEqual(["Catherine Stone", "Paul Stone"], children_names)
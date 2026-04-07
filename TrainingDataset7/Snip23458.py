def test_add(self):
        category_id = Category.objects.create(name="male").pk
        prefix = "generic_inline_admin-phonenumber-content_type-object_id"
        post_data = {
            "name": "John Doe",
            # inline data
            f"{prefix}-TOTAL_FORMS": "1",
            f"{prefix}-INITIAL_FORMS": "0",
            f"{prefix}-MAX_NUM_FORMS": "0",
            f"{prefix}-0-id": "",
            f"{prefix}-0-phone_number": "555-555-5555",
            f"{prefix}-0-category": str(category_id),
        }
        response = self.client.get(reverse("admin:generic_inline_admin_contact_add"))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(
            reverse("admin:generic_inline_admin_contact_add"), post_data
        )
        self.assertEqual(response.status_code, 302)
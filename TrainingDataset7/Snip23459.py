def test_delete(self):
        from .models import Contact

        c = Contact.objects.create(name="foo")
        PhoneNumber.objects.create(
            object_id=c.id,
            content_type=ContentType.objects.get_for_model(Contact),
            phone_number="555-555-5555",
        )
        response = self.client.post(
            reverse("admin:generic_inline_admin_contact_delete", args=[c.pk])
        )
        self.assertContains(response, "Are you sure you want to delete")
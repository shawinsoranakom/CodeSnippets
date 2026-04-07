def test_invalid_reverse_m2m_field_with_related_name(self):
        class Contact(Model):
            pass

        class Customer(Model):
            contacts = ManyToManyField("Contact", related_name="customers")

        class TestModelAdmin(ModelAdmin):
            filter_horizontal = ["customers"]

        self.assertIsInvalid(
            TestModelAdmin,
            Contact,
            "The value of 'filter_horizontal[0]' must be a many-to-many field.",
            "admin.E020",
        )
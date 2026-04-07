def test_update_m2m_field(self):
        rel = "<django.db.models.fields.related.ManyToManyField: m2m_foo>"
        msg = f"Cannot update model field {rel} (only concrete fields are permitted)."
        with self.assertRaisesMessage(FieldError, msg):
            Bar.objects.update(m2m_foo="whatever")
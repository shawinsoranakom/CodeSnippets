def test_update_reverse_m2m_descriptor(self):
        rel = "<ManyToManyRel: update.bar>"
        msg = f"Cannot update model field {rel} (only concrete fields are permitted)."
        with self.assertRaisesMessage(FieldError, msg):
            Foo.objects.update(m2m_foo="whatever")
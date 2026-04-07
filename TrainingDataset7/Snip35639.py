def test_update_reverse_fk_descriptor(self):
        rel = "<ManyToOneRel: update.bar>"
        msg = f"Cannot update model field {rel} (only concrete fields are permitted)."
        with self.assertRaisesMessage(FieldError, msg):
            Foo.objects.update(bar="whatever")
def test_update_reverse_o2o_descriptor(self):
        rel = "<OneToOneRel: update.bar>"
        msg = f"Cannot update model field {rel} (only concrete fields are permitted)."
        with self.assertRaisesMessage(FieldError, msg):
            Foo.objects.update(o2o_bar="whatever")
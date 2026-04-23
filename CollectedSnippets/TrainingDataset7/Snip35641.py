def test_update_reverse_mti_parent_link_descriptor(self):
        rel = "<OneToOneRel: update.uniquenumberchild>"
        msg = f"Cannot update model field {rel} (only concrete fields are permitted)."
        with self.assertRaisesMessage(FieldError, msg):
            UniqueNumber.objects.update(uniquenumberchild="whatever")
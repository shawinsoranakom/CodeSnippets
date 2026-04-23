def test_internal_related_name_not_in_error_msg(self):
        # The secret internal related names for self-referential many-to-many
        # fields shouldn't appear in the list when an error is made.
        msg = (
            "Choices are: id, name, references, related, selfreferchild, "
            "selfreferchildsibling"
        )
        with self.assertRaisesMessage(FieldError, msg):
            SelfRefer.objects.filter(porcupine="fred")
def test_reverse_field_name_disallowed(self):
        """
        If a related_name is given you can't use the field name instead
        """
        msg = (
            "Cannot resolve keyword 'choice' into field. Choices are: "
            "creator, creator_id, id, poll_choice, question, related_choice"
        )
        with self.assertRaisesMessage(FieldError, msg):
            Poll.objects.get(choice__name__exact="This is the answer")
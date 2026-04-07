def test_custom_field_with_queryset_but_no_limit_choices_to(self):
        """
        A custom field with a `queryset` attribute but no `limit_choices_to`
        works (#23795).
        """
        f = StumpJokeWithCustomFieldForm()
        self.assertEqual(f.fields["custom"].queryset, 42)
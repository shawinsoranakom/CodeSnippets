def test_pk_must_be_list_or_tuple(self):
        user = User.objects.get(pk=self.user.pk)
        test_cases = [
            "foo",
            1000,
            3.14,
            True,
            False,
        ]

        for pk in test_cases:
            with self.assertRaisesMessage(
                ValueError, "'pk' must be a list or a tuple."
            ):
                user.pk = pk
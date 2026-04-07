def test_pk_must_have_2_elements(self):
        user = User.objects.get(pk=self.user.pk)
        test_cases = [
            (),
            [],
            (1000,),
            [1000],
            (1, 2, 3),
            [1, 2, 3],
        ]

        for pk in test_cases:
            with self.assertRaisesMessage(ValueError, "'pk' must have 2 elements."):
                user.pk = pk
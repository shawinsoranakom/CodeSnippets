def test_validate_unique(self):
        user = User.objects.get(pk=self.user_1.pk)
        user.id = None

        with self.assertRaises(ValidationError) as ctx:
            user.validate_unique()

        self.assertSequenceEqual(
            ctx.exception.messages, ("User with this Email already exists.",)
        )
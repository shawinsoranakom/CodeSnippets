def _test_confirm_start(self):
        # instead of fixture
        UUIDUser.objects.create_user(
            email=self.user_email,
            username="foo",
            password="foo",
        )
        return super()._test_confirm_start()
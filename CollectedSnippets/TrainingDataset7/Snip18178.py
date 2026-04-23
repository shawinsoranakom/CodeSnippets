def test_int(self):
        msg = (
            "Cannot cast AnonymousUser to int. Are you trying to use it in "
            "place of User?"
        )
        with self.assertRaisesMessage(TypeError, msg):
            int(self.user)
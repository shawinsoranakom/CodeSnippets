def test_is_active_field_default(self):
        """
        tests that the default value for is_active is provided
        """
        UserModel = get_user_model()
        user = UserModel(username="foo")
        self.assertIs(user.is_active, True)
        # you can set the attribute - but it will not save
        user.is_active = False
        # there should be no problem saving - but the attribute is not saved
        user.save()
        user_fetched = UserModel._default_manager.get(pk=user.pk)
        # the attribute is always true for newly retrieved instance
        self.assertIs(user_fetched.is_active, True)
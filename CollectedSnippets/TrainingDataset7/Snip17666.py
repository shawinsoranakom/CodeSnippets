def test_user_attrs(self):
        """
        The lazy objects returned behave just like the wrapped objects.
        """
        # These are 'functional' level tests for common use cases. Direct
        # testing of the implementation (SimpleLazyObject) is in the 'utils'
        # tests.
        self.client.login(username="super", password="secret")
        user = authenticate(username="super", password="secret")
        response = self.client.get("/auth_processor_user/")
        self.assertContains(response, "unicode: super")
        self.assertContains(response, "id: %s" % self.superuser.pk)
        self.assertContains(response, "username: super")
        # bug #12037 is tested by the {% url %} in the template:
        self.assertContains(response, "url: /userpage/super/")

        # A Q() comparing a user and with another Q() (in an AND or OR
        # fashion).
        Q(user=response.context["user"]) & Q(someflag=True)

        # Tests for user equality. This is hard because User defines
        # equality in a non-duck-typing way
        # See bug #12060
        self.assertEqual(response.context["user"], user)
        self.assertEqual(user, response.context["user"])
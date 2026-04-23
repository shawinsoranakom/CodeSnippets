def test_user_passes_test_composition(self):
        """
        The user_passes_test decorator can be applied multiple times (#9474).
        """

        def test1(user):
            user.decorators_applied.append("test1")
            return True

        def test2(user):
            user.decorators_applied.append("test2")
            return True

        def callback(request):
            return request.user.decorators_applied

        callback = user_passes_test(test1)(callback)
        callback = user_passes_test(test2)(callback)

        class DummyUser:
            pass

        class DummyRequest:
            pass

        request = DummyRequest()
        request.user = DummyUser()
        request.user.decorators_applied = []
        response = callback(request)

        self.assertEqual(response, ["test2", "test1"])
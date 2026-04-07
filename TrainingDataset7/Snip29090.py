def test_has_view_permission(self):
        """
        has_view_permission() returns True for users who can view objects and
        False for users who can't.
        """
        ma = ModelAdmin(Band, AdminSite())
        request = MockRequest()
        request.user = self.MockViewUser()
        self.assertIs(ma.has_view_permission(request), True)
        request.user = self.MockAddUser()
        self.assertIs(ma.has_view_permission(request), False)
        request.user = self.MockChangeUser()
        self.assertIs(ma.has_view_permission(request), True)
        request.user = self.MockDeleteUser()
        self.assertIs(ma.has_view_permission(request), False)
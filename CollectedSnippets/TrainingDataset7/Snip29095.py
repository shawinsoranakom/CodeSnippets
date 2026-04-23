def test_has_module_permission(self):
        """
        as_module_permission returns True for users who have any permission
        for the module and False for users who don't.
        """
        ma = ModelAdmin(Band, AdminSite())
        request = MockRequest()
        request.user = self.MockViewUser()
        self.assertIs(ma.has_module_permission(request), True)
        request.user = self.MockAddUser()
        self.assertTrue(ma.has_module_permission(request))
        request.user = self.MockChangeUser()
        self.assertTrue(ma.has_module_permission(request))
        request.user = self.MockDeleteUser()
        self.assertTrue(ma.has_module_permission(request))

        original_app_label = ma.opts.app_label
        ma.opts.app_label = "anotherapp"
        try:
            request.user = self.MockViewUser()
            self.assertIs(ma.has_module_permission(request), False)
            request.user = self.MockAddUser()
            self.assertFalse(ma.has_module_permission(request))
            request.user = self.MockChangeUser()
            self.assertFalse(ma.has_module_permission(request))
            request.user = self.MockDeleteUser()
            self.assertFalse(ma.has_module_permission(request))
        finally:
            ma.opts.app_label = original_app_label
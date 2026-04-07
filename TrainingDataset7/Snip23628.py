def test_calling_more_than_once(self):
        """
        Test a view can only be called once.
        """
        request = self.rf.get("/")
        view = InstanceView.as_view()
        self.assertNotEqual(view(request), view(request))
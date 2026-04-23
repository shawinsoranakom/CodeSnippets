def test_process_view_middleware(self):
        """
        Test a middleware that implements process_view.
        """
        process_view(self.rf.get("/"))
def test_callable_process_view_middleware(self):
        """
        Test a middleware that implements process_view, operating on a callable
        class.
        """
        class_process_view(self.rf.get("/"))
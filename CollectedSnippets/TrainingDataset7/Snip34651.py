def test_exception_following_nested_client_request(self):
        """
        A nested test client request shouldn't clobber exception signals from
        the outer client request.
        """
        with self.assertRaisesMessage(Exception, "exception message"):
            self.client.get("/nesting_exception_view/")
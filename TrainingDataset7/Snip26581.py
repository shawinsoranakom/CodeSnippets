def test_append_slash_no_redirect_in_DEBUG(self):
        """
        While in debug mode, an exception is raised with a warning
        when a failed attempt is made to DELETE, POST, PUT, or PATCH to an URL
        which would normally be redirected to a slashed version.
        """
        msg = "maintaining %s data. Change your form to point to testserver/slash/"
        request = self.rf.get("/slash")
        request.method = "POST"
        with self.assertRaisesMessage(RuntimeError, msg % request.method):
            CommonMiddleware(get_response_404)(request)
        request = self.rf.get("/slash")
        request.method = "PUT"
        with self.assertRaisesMessage(RuntimeError, msg % request.method):
            CommonMiddleware(get_response_404)(request)
        request = self.rf.get("/slash")
        request.method = "PATCH"
        with self.assertRaisesMessage(RuntimeError, msg % request.method):
            CommonMiddleware(get_response_404)(request)
        request = self.rf.delete("/slash")
        with self.assertRaisesMessage(RuntimeError, msg % request.method):
            CommonMiddleware(get_response_404)(request)
def test_file_error_blocking(self):
        """
        The server should not block when there are upload errors (bug #8622).
        This can happen if something -- i.e. an exception handler -- tries to
        access POST while handling an error in parsing POST. This shouldn't
        cause an infinite loop!
        """

        class POSTAccessingHandler(client.ClientHandler):
            """A handler that'll access POST during an exception."""

            def handle_uncaught_exception(self, request, resolver, exc_info):
                ret = super().handle_uncaught_exception(request, resolver, exc_info)
                request.POST  # evaluate
                return ret

        # Maybe this is a little more complicated that it needs to be; but if
        # the django.test.client.FakePayload.read() implementation changes then
        # this test would fail. So we need to know exactly what kind of error
        # it raises when there is an attempt to read more than the available
        # bytes:
        try:
            client.FakePayload(b"a").read(2)
        except Exception as err:
            reference_error = err

        # install the custom handler that tries to access request.POST
        self.client.handler = POSTAccessingHandler()

        with open(__file__, "rb") as fp:
            post_data = {
                "name": "Ringo",
                "file_field": fp,
            }
            try:
                self.client.post("/upload_errors/", post_data)
            except reference_error.__class__ as err:
                self.assertNotEqual(
                    str(err),
                    str(reference_error),
                    "Caught a repeated exception that'll cause an infinite loop in "
                    "file uploads.",
                )
            except Exception as err:
                # CustomUploadError is the error that should have been raised
                self.assertEqual(err.__class__, uploadhandler.CustomUploadError)
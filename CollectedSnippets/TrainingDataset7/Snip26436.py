def test_repr(self):
        request = self.get_request()
        storage = self.storage_class(request)
        self.assertEqual(
            repr(storage),
            f"<{self.storage_class.__qualname__}: request=<HttpRequest>>",
        )
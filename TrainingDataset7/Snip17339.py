async def test_meta_not_modified_with_repeat_headers(self):
        scope = self.async_request_factory._base_scope(path="/", http_version="2.0")
        scope["headers"] = [(b"foo", b"bar")] * 200_000

        setitem_count = 0

        class InstrumentedDict(dict):
            def __setitem__(self, *args, **kwargs):
                nonlocal setitem_count
                setitem_count += 1
                super().__setitem__(*args, **kwargs)

        class InstrumentedASGIRequest(ASGIRequest):
            @property
            def META(self):
                return self._meta

            @META.setter
            def META(self, value):
                self._meta = InstrumentedDict(**value)

        request = InstrumentedASGIRequest(scope, None)

        self.assertEqual(len(request.headers["foo"].split(",")), 200_000)
        self.assertLessEqual(setitem_count, 100)
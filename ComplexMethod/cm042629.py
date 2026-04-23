def test_should_remove_req_res_references_before_caching_the_results(self):
        """Regression test case to prevent a memory leak in the Media Pipeline.

        The memory leak is triggered when an exception is raised when a Response
        scheduled by the Media Pipeline is being returned. For example, when a
        FileException('download-error') is raised because the Response status
        code is not 200 OK.

        It happens because we are keeping a reference to the Response object
        inside the FileException context. This is caused by the way Twisted
        return values from inline callbacks. It raises a custom exception
        encapsulating the original return value.

        The solution is to remove the exception context when this context is a
        _DefGen_Return instance, the BaseException used by Twisted to pass the
        returned value from those inline callbacks.

        Maybe there's a better and more reliable way to test the case described
        here, but it would be more complicated and involve running - or at least
        mocking - some async steps from the Media Pipeline. The current test
        case is simple and detects the problem very fast. On the other hand, it
        would not detect another kind of leak happening due to old object
        references being kept inside the Media Pipeline cache.

        This problem does not occur in Python 2.7 since we don't have Exception
        Chaining (https://www.python.org/dev/peps/pep-3134/).
        """
        # Create sample pair of Request and Response objects
        request = Request("http://url")
        response = Response("http://url", body=b"", request=request)

        # Simulate the Media Pipeline behavior to produce a Twisted Failure
        try:
            # Simulate a Twisted inline callback returning a Response
            raise StopIteration(response)
        except StopIteration as exc:
            def_gen_return_exc = exc
            try:
                # Simulate the media_downloaded callback raising a FileException
                # This usually happens when the status code is not 200 OK
                raise FileException("download-error")
            except Exception as exc:
                file_exc = exc
                # Simulate Twisted capturing the FileException
                # It encapsulates the exception inside a Twisted Failure
                failure = Failure(file_exc)

        # The Failure should encapsulate a FileException ...
        assert failure.value == file_exc
        # ... and it should have the StopIteration exception set as its context
        assert failure.value.__context__ == def_gen_return_exc

        # Let's calculate the request fingerprint and fake some runtime data...
        fp = self.fingerprint(request)
        info = self.pipe.spiderinfo
        info.downloading.add(fp)
        info.waiting[fp] = []

        # When calling the method that caches the Request's result ...
        self.pipe._cache_result_and_execute_waiters(failure, fp, info)
        # ... it should store the Twisted Failure ...
        assert info.downloaded[fp] == failure
        # ... encapsulating the original FileException ...
        assert info.downloaded[fp].value == file_exc
        # ... but it should not store the StopIteration exception on its context
        context = getattr(info.downloaded[fp].value, "__context__", None)
        assert context is None
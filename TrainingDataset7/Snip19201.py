def test_touch(self):
        """Override to manually advance time since file access can be slow."""

        class ManualTickingTime:
            def __init__(self):
                # Freeze time, calling `sleep` will manually advance it.
                self._time = time.time()

            def time(self):
                return self._time

            def sleep(self, seconds):
                self._time += seconds

        mocked_time = ManualTickingTime()
        with (
            mock.patch("django.core.cache.backends.filebased.time", new=mocked_time),
            mock.patch("django.core.cache.backends.base.time", new=mocked_time),
            mock.patch("cache.tests.time", new=mocked_time),
        ):
            super().test_touch()
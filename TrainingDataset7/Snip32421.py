def setUpClass(cls):
        # If contrib.staticfiles isn't configured properly, the exception
        # should bubble up to the main thread.
        old_STATIC_URL = TEST_SETTINGS["STATIC_URL"]
        TEST_SETTINGS["STATIC_URL"] = None
        try:
            cls.raises_exception()
        finally:
            TEST_SETTINGS["STATIC_URL"] = old_STATIC_URL
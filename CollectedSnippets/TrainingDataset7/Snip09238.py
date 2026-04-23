def _mark_test(self, test_name, skip_reason=None):
        # Only load unittest during testing.
        from unittest import expectedFailure, skip

        module_or_class_name, _, name_to_mark = test_name.rpartition(".")
        test_app = test_name.split(".")[0]
        # Importing a test app that isn't installed raises RuntimeError.
        if test_app in settings.INSTALLED_APPS:
            try:
                test_frame = import_string(module_or_class_name)
            except ImportError:
                # import_string() can raise ImportError if a submodule's parent
                # module hasn't already been imported during test discovery.
                # This can happen in at least two cases:
                # 1. When running a subset of tests in a module, the test
                #    runner won't import tests in that module's other
                #    submodules.
                # 2. When the parallel test runner spawns workers with an empty
                #    import cache.
                test_to_mark = import_string(test_name)
                test_frame = sys.modules.get(test_to_mark.__module__)
            else:
                test_to_mark = getattr(test_frame, name_to_mark)
            if skip_reason:
                setattr(test_frame, name_to_mark, skip(skip_reason)(test_to_mark))
            else:
                setattr(test_frame, name_to_mark, expectedFailure(test_to_mark))
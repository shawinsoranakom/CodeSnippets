def files_to_test(cls):

        if cls._files_to_test is not None:
            return cls._files_to_test

        items = [
            item.resolve()
            for directory in cls.test_directories
            for item in directory.glob("*.py")
            if not item.name.startswith("bad")
        ]

        # Test limited subset of files unless the 'cpu' resource is specified.
        if not test.support.is_resource_enabled("cpu"):

            tests_to_run_always = {item for item in items if
                                   item.name in cls.run_always_files}

            items = set(random.sample(items, 10))

            # Make sure that at least tests that heavily use grammar features are
            # always considered in order to reduce the chance of missing something.
            items = list(items | tests_to_run_always)

        # bpo-31174: Store the names sample to always test the same files.
        # It prevents false alarms when hunting reference leaks.
        cls._files_to_test = items

        return items
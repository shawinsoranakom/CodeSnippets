def setUp(self):
        modules = [
            "DUMMY_MODULE_1",
            "DUMMY_MODULE_2",
            "MISBEHAVED_MODULE",
            "NESTED_MODULE_PARENT",
            "NESTED_MODULE_CHILD",
        ]

        the_globals = globals()

        for name in modules:
            try:
                del sys.modules[the_globals[name].__name__]
            except:
                pass

            try:
                del sys.modules[name]
            except:
                pass
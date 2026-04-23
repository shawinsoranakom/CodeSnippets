def test_get_new_defined(self):
        """
        Ensure `old` complains and not `new` when only `new` is defined.
        """

        class Manager(metaclass=RenameManagerMethods):
            def new(self):
                pass

        manager = Manager()

        with warnings.catch_warnings(record=True) as recorded:
            warnings.simplefilter("always")
            manager.new()
        self.assertEqual(len(recorded), 0)

        msg = "`Manager.old` is deprecated, use `new` instead."
        with self.assertWarnsMessage(DeprecationWarning, msg) as ctx:
            manager.old()
        self.assertEqual(ctx.filename, __file__)
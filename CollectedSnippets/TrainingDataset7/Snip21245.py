def test_get_old_defined(self):
        """
        Ensure `old` complains when only `old` is defined.
        """
        msg = "`Manager.old` method should be renamed `new`."
        with self.assertWarnsMessage(DeprecationWarning, msg) as ctx:

            class Manager(metaclass=RenameManagerMethods):
                def old(self):
                    pass

        self.assertEqual(ctx.filename, __file__)

        manager = Manager()

        with warnings.catch_warnings(record=True) as recorded:
            warnings.simplefilter("always")
            manager.new()
        self.assertEqual(len(recorded), 0)

        msg = "`Manager.old` is deprecated, use `new` instead."
        with self.assertWarnsMessage(DeprecationWarning, msg) as ctx:
            manager.old()
        self.assertEqual(ctx.filename, __file__)
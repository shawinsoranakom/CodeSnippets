def test_renamed_subclass_deprecated(self):
        """
        Ensure the correct warnings are raised when a class that renamed
        `old` subclass one that didn't.
        """
        msg = "`Deprecated.old` method should be renamed `new`."
        with self.assertWarnsMessage(DeprecationWarning, msg) as ctx:

            class Deprecated(metaclass=RenameManagerMethods):
                def old(self):
                    pass

        self.assertEqual(ctx.filename, __file__)

        class Renamed(Deprecated):
            def new(self):
                super().new()

        renamed = Renamed()

        with warnings.catch_warnings(record=True) as recorded:
            warnings.simplefilter("always")
            renamed.new()
        self.assertEqual(len(recorded), 0)

        msg = "`Renamed.old` is deprecated, use `new` instead."
        with self.assertWarnsMessage(DeprecationWarning, msg) as ctx:
            renamed.old()
        self.assertEqual(ctx.filename, __file__)
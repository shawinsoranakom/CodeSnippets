def test_deprecated_subclass_renamed(self):
        """
        Ensure the correct warnings are raised when a class that didn't rename
        `old` subclass one that did.
        """

        class Renamed(metaclass=RenameManagerMethods):
            def new(self):
                pass

        msg = "`Deprecated.old` method should be renamed `new`."
        with self.assertWarnsMessage(DeprecationWarning, msg) as ctx:

            class Deprecated(Renamed):
                def old(self):
                    super().old()

        self.assertEqual(ctx.filename, __file__)

        deprecated = Deprecated()

        msg = "`Renamed.old` is deprecated, use `new` instead."
        with self.assertWarnsMessage(DeprecationWarning, msg) as ctx:
            deprecated.new()
        self.assertEqual(ctx.filename, __file__)

        msg = "`Deprecated.old` is deprecated, use `new` instead."
        with self.assertWarnsMessage(DeprecationWarning, msg) as ctx:
            deprecated.old()
        self.assertEqual(ctx.filename, __file__)
def test_deprecated_subclass_renamed_and_mixins(self):
        """
        Ensure the correct warnings are raised when a subclass inherit from a
        class that renamed `old` and mixins that may or may not have renamed
        `new`.
        """

        class Renamed(metaclass=RenameManagerMethods):
            def new(self):
                pass

        class RenamedMixin:
            def new(self):
                super().new()

        class DeprecatedMixin:
            def old(self):
                super().old()

        msg = "`DeprecatedMixin.old` method should be renamed `new`."
        with self.assertWarnsMessage(DeprecationWarning, msg) as ctx:

            class Deprecated(DeprecatedMixin, RenamedMixin, Renamed):
                pass

        self.assertEqual(ctx.filename, __file__)

        deprecated = Deprecated()

        msg = "`RenamedMixin.old` is deprecated, use `new` instead."
        with self.assertWarnsMessage(DeprecationWarning, msg) as ctx:
            deprecated.new()
        self.assertEqual(ctx.filename, __file__)

        msg = "`DeprecatedMixin.old` is deprecated, use `new` instead."
        with self.assertWarnsMessage(DeprecationWarning, msg) as ctx:
            deprecated.old()
        self.assertEqual(ctx.filename, __file__)
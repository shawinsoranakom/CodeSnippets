def test_class_definition_warnings(self):
        """
        Ensure a warning is raised upon class definition to suggest renaming
        the faulty method.
        """
        msg = "`Manager.old` method should be renamed `new`."
        with self.assertWarnsMessage(DeprecationWarning, msg) as ctx:

            class Manager(metaclass=RenameManagerMethods):
                def old(self):
                    pass

        self.assertEqual(ctx.filename, __file__)
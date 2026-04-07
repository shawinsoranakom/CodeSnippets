def test_unimportable_serializer(self):
        """
        Failing serializer import raises the proper error
        """
        with self.assertRaisesMessage(ImportError, "No module named 'unexistent'"):
            management.call_command(
                "loaddata",
                "bad_fix.ture1.unkn",
                verbosity=0,
            )
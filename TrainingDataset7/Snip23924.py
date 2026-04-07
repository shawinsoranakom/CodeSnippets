def test_error_contains_full_traceback(self):
        """
        update_or_create should raise IntegrityErrors with the full traceback.
        This is tested by checking that a known method call is in the
        traceback. We cannot use assertRaises/assertRaises here because we need
        to inspect the actual traceback. Refs #16340.
        """
        try:
            ManualPrimaryKeyTest.objects.update_or_create(id=1, data="Different")
        except IntegrityError:
            formatted_traceback = traceback.format_exc()
            self.assertIn("obj.save", formatted_traceback)
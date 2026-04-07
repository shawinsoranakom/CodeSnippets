def test_lazy_object_is_not_evaluated_before_manual_access(self):
        obj = Storage()
        self.assertIs(obj.lazy_storage.storage._wrapped, empty)
        # assertEqual triggers resolution.
        self.assertEqual(obj.lazy_storage.storage, temp_storage)
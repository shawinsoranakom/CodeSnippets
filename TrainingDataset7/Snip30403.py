def test_unsaved_obj(self):
        msg = "QuerySet.contains() cannot be used on unsaved objects."
        with self.assertRaisesMessage(ValueError, msg):
            DumbCategory.objects.contains(DumbCategory())
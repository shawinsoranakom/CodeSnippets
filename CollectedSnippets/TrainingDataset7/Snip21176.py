def test_disallowed_delete_distinct_on(self):
        msg = "Cannot call delete() after .distinct(*fields)."
        with self.assertRaisesMessage(TypeError, msg):
            Book.objects.distinct("id").delete()
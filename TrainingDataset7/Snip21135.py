def test_fast_delete_instance_set_pk_none(self):
        u = User.objects.create()
        # User can be fast-deleted.
        collector = Collector(using="default")
        self.assertTrue(collector.can_fast_delete(u))
        u.delete()
        self.assertIsNone(u.pk)
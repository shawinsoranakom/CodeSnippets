def test_cached_relation_invalidated_on_save(self):
        """
        Model.save() invalidates stale ForeignKey relations after a primary key
        assignment.
        """
        self.assertEqual(self.a.reporter, self.r)  # caches a.reporter
        self.a.reporter_id = self.r2.pk
        self.a.save()
        self.assertEqual(self.a.reporter, self.r2)
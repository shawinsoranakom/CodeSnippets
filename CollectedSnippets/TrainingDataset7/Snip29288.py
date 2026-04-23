def test_cached_relation_invalidated_on_save(self):
        """
        Model.save() invalidates stale OneToOneField relations after a primary
        key assignment.
        """
        self.assertEqual(self.b1.place, self.p1)  # caches b1.place
        self.b1.place_id = self.p2.pk
        self.b1.save()
        self.assertEqual(self.b1.place, self.p2)
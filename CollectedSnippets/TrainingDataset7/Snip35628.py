def test_foreign_key_update_with_id(self):
        """
        Update works using <field>_id for foreign keys
        """
        num_updated = self.a1.d_set.update(a_id=self.a2)
        self.assertEqual(num_updated, 20)
        self.assertEqual(self.a2.d_set.count(), 20)
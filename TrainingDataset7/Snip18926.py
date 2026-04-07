def test_specified_parent_hash_inherited(self):
        class ParentHash(models.Model):
            def __eq__(self, other):
                return super.__eq__(other)

            __hash__ = models.Model.__hash__

        self.assertEqual(hash(ParentHash(id=1)), 1)
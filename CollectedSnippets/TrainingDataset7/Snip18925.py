def test_missing_hash_not_inherited(self):
        class NoHash(models.Model):
            def __eq__(self, other):
                return super.__eq__(other)

        with self.assertRaisesMessage(TypeError, "unhashable type: 'NoHash'"):
            hash(NoHash(id=1))
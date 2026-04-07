def test_hash_immutability(self):
        field = models.IntegerField()
        field_hash = hash(field)

        class MyModel(models.Model):
            rank = field

        self.assertEqual(field_hash, hash(field))
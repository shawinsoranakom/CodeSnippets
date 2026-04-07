def test_hash(self):
        # Value based on PK
        self.assertEqual(hash(Article(id=1)), hash(1))
        msg = "Model instances without primary key value are unhashable"
        with self.assertRaisesMessage(TypeError, msg):
            # No PK value -> unhashable (because save() would then change
            # hash)
            hash(Article())
def test_hash(self):
        self.assertEqual(hash(User(pk=(1, 2))), hash((1, 2)))
        self.assertEqual(hash(User(tenant_id=2, id=3)), hash((2, 3)))
        msg = "Model instances without primary key value are unhashable"

        with self.assertRaisesMessage(TypeError, msg):
            hash(User())
        with self.assertRaisesMessage(TypeError, msg):
            hash(User(tenant_id=1))
        with self.assertRaisesMessage(TypeError, msg):
            hash(User(id=1))
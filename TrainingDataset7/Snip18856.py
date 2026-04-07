def test_zero_as_autoval(self):
        msg = "The database backend does not accept 0 as a value for AutoField."
        with self.assertRaisesMessage(ValueError, msg):
            Square.objects.create(id=0, root=0, square=1)
        with self.assertRaisesMessage(ValueError, msg):
            Square.objects.create(id=Value(0, BigAutoField()), root=0, square=1)
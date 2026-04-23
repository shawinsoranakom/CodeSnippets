def test_pk_none(self):
        m = M()
        msg = "M object can't be deleted because its id attribute is set to None."
        with self.assertRaisesMessage(ValueError, msg):
            m.delete()
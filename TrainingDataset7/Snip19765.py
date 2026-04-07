def test_remove_sql(self):
        c = BaseConstraint(name="name")
        msg = "This method must be implemented by a subclass."
        with self.assertRaisesMessage(NotImplementedError, msg):
            c.remove_sql(None, None)
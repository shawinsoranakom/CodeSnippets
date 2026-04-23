def test_get_constraints(self):
        msg = self.may_require_msg % "get_constraints"
        with self.assertRaisesMessage(NotImplementedError, msg):
            self.introspection.get_constraints(None, None)
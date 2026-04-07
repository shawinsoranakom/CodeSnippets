def test_get_relations(self):
        msg = self.may_require_msg % "get_relations"
        with self.assertRaisesMessage(NotImplementedError, msg):
            self.introspection.get_relations(None, None)
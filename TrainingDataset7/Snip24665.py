def test_unit_att_name_invalid(self):
        msg = "Unknown unit type: invalid-unit-name"
        with self.assertRaisesMessage(AttributeError, msg):
            D.unit_attname("invalid-unit-name")
        with self.assertRaisesMessage(AttributeError, msg):
            A.unit_attname("invalid-unit-name")
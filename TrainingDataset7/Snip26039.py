def test_m2m_relations_unusable_on_null_to_field(self):
        nullcar = Car(make=None)
        msg = (
            '"<Car: None>" needs to have a value for field "make" before this '
            "many-to-many relationship can be used."
        )
        with self.assertRaisesMessage(ValueError, msg):
            nullcar.drivers.all()
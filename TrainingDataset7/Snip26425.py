def test_unsaved(self):
        msg = (
            "'Car' instance needs to have a primary key value before this relationship "
            "can be used."
        )
        with self.assertRaisesMessage(ValueError, msg):
            Car(make="Ford").drivers.all()
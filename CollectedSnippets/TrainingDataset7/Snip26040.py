def test_m2m_relations_unusable_on_null_pk_obj(self):
        msg = (
            "'Car' instance needs to have a primary key value before a "
            "many-to-many relationship can be used."
        )
        with self.assertRaisesMessage(ValueError, msg):
            Car(make="Ford").drivers.all()
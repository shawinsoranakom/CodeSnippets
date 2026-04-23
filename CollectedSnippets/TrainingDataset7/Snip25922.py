def test_m2m_pk_field_type(self):
        # Regression for #11311 - The primary key for models in a m2m relation
        # doesn't have to be an AutoField

        w = Worksheet(id="abc")
        w.save()
        w.delete()
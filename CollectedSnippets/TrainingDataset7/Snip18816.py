def test_sequence_name_length_limits_m2m(self):
        """
        An m2m save of a model with a long name and a long m2m field name
        doesn't error (#8901).
        """
        obj = (
            VeryLongModelNameZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ.objects.create()
        )
        rel_obj = Person.objects.create(first_name="Django", last_name="Reinhardt")
        obj.m2m_also_quite_long_zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz.add(rel_obj)
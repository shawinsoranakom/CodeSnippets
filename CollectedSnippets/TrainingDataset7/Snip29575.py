def test_in_including_F_object(self):
        # This test asserts that Array objects passed to filters can be
        # constructed to contain F objects. This currently doesn't work as the
        # psycopg mogrify method that generates the ARRAY() syntax is
        # expecting literals, not column references (#27095).
        self.assertSequenceEqual(
            NullableIntegerArrayModel.objects.filter(field__in=[[models.F("id")]]),
            self.objs[:2],
        )
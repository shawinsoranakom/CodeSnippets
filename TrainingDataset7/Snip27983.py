def test_db_check_constraints(self):
        value = "{@!invalid json value 123 $!@#"
        with mock.patch.object(DjangoJSONEncoder, "encode", return_value=value):
            with self.assertRaises((IntegrityError, DataError, OperationalError)):
                NullableJSONModel.objects.create(value_custom=value)
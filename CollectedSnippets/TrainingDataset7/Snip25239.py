def test_number_field_types(self):
        """Test introspection of various Django field types"""
        assertFieldType = self.make_field_type_asserter()
        introspected_field_types = connection.features.introspected_field_types

        auto_field_type = connection.features.introspected_field_types["AutoField"]
        if auto_field_type != "AutoField":
            assertFieldType(
                "id", "models.%s(primary_key=True)  # AutoField?" % auto_field_type
            )

        assertFieldType(
            "big_int_field", "models.%s()" % introspected_field_types["BigIntegerField"]
        )

        bool_field_type = introspected_field_types["BooleanField"]
        assertFieldType("bool_field", "models.{}()".format(bool_field_type))
        assertFieldType(
            "null_bool_field",
            "models.{}(blank=True, null=True)".format(bool_field_type),
        )

        if connection.vendor != "sqlite":
            assertFieldType(
                "decimal_field", "models.DecimalField(max_digits=6, decimal_places=1)"
            )
        else:
            assertFieldType("decimal_field", "models.DecimalField()")

        assertFieldType("float_field", "models.FloatField()")
        assertFieldType(
            "int_field", "models.%s()" % introspected_field_types["IntegerField"]
        )
        assertFieldType(
            "pos_int_field",
            "models.%s()" % introspected_field_types["PositiveIntegerField"],
        )
        assertFieldType(
            "pos_big_int_field",
            "models.%s()" % introspected_field_types["PositiveBigIntegerField"],
        )
        assertFieldType(
            "pos_small_int_field",
            "models.%s()" % introspected_field_types["PositiveSmallIntegerField"],
        )
        assertFieldType(
            "small_int_field",
            "models.%s()" % introspected_field_types["SmallIntegerField"],
        )
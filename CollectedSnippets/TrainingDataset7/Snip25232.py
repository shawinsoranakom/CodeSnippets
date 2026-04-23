def test_field_types(self):
        """Test introspection of various Django field types"""
        assertFieldType = self.make_field_type_asserter()
        introspected_field_types = connection.features.introspected_field_types
        char_field_type = introspected_field_types["CharField"]
        # Inspecting Oracle DB doesn't produce correct results (#19884):
        # - it reports fields as blank=True when they aren't.
        if (
            not connection.features.interprets_empty_strings_as_nulls
            and char_field_type == "CharField"
        ):
            assertFieldType("char_field", "models.CharField(max_length=10)")
            assertFieldType(
                "null_char_field",
                "models.CharField(max_length=10, blank=True, null=True)",
            )
            assertFieldType("email_field", "models.CharField(max_length=254)")
            assertFieldType("file_field", "models.CharField(max_length=100)")
            assertFieldType("file_path_field", "models.CharField(max_length=100)")
            assertFieldType("slug_field", "models.CharField(max_length=50)")
            assertFieldType("text_field", "models.TextField()")
            assertFieldType("url_field", "models.CharField(max_length=200)")
        if char_field_type == "TextField":
            assertFieldType("char_field", "models.TextField()")
            assertFieldType(
                "null_char_field", "models.TextField(blank=True, null=True)"
            )
            assertFieldType("email_field", "models.TextField()")
            assertFieldType("file_field", "models.TextField()")
            assertFieldType("file_path_field", "models.TextField()")
            assertFieldType("slug_field", "models.TextField()")
            assertFieldType("text_field", "models.TextField()")
            assertFieldType("url_field", "models.TextField()")
        assertFieldType("date_field", "models.DateField()")
        assertFieldType("date_time_field", "models.DateTimeField()")
        if introspected_field_types["GenericIPAddressField"] == "GenericIPAddressField":
            assertFieldType("gen_ip_address_field", "models.GenericIPAddressField()")
        elif not connection.features.interprets_empty_strings_as_nulls:
            assertFieldType("gen_ip_address_field", "models.CharField(max_length=39)")
        assertFieldType(
            "time_field", "models.%s()" % introspected_field_types["TimeField"]
        )
        if connection.features.has_native_uuid_field:
            assertFieldType("uuid_field", "models.UUIDField()")
        elif not connection.features.interprets_empty_strings_as_nulls:
            assertFieldType("uuid_field", "models.CharField(max_length=32)")
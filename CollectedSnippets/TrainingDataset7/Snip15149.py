def test_exact_lookup_validates_each_field_independently(self):
        """
        Each field validates the search term independently without leaking
        converted values between fields.

        "3." is valid for IntegerField (converts to 3) but invalid for
        JSONField. The converted value must not leak to the JSONField check.
        """
        # obj_int has int_field=3, should match "3." via IntegerField.
        obj_int = MixedFieldsModel.objects.create(
            int_field=3, json_field={"key": "value"}
        )
        # obj_json has json_field=3, should NOT match "3." because "3." is
        # invalid JSON.
        MixedFieldsModel.objects.create(int_field=99, json_field=3)
        m = admin.ModelAdmin(MixedFieldsModel, custom_site)
        m.search_fields = ["int_field__exact", "json_field__exact"]

        # "3." is valid for int (becomes 3) but invalid JSON.
        # Only obj_int should match via int_field.
        request = self.factory.get("/", data={SEARCH_VAR: "3."})
        request.user = self.superuser

        cl = m.get_changelist_instance(request)
        self.assertCountEqual(cl.queryset, [obj_int])
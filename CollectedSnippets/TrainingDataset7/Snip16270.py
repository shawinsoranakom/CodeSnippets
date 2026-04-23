def get_admin_readonly_field(self, response, field_name):
        """
        Return the readonly field for the given field_name.
        """
        admin_readonly_fields = self.get_admin_readonly_fields(response)
        for field in admin_readonly_fields:
            if field.field["name"] == field_name:
                return field
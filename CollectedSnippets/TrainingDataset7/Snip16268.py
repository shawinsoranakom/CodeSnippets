def get_admin_form_fields(self, response):
        """
        Return a list of AdminFields for the AdminForm in the response.
        """
        fields = []
        for fieldset in response.context["adminform"]:
            for field_line in fieldset:
                fields.extend(field_line)
        return fields
def get_admin_readonly_fields(self, response):
        """
        Return the readonly fields for the response's AdminForm.
        """
        return [f for f in self.get_admin_form_fields(response) if f.is_readonly]
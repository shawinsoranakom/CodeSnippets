def auto_id(self):
        """
        Calculate and return the ID attribute for this BoundField, if the
        associated Form has specified auto_id. Return an empty string
        otherwise.
        """
        auto_id = self.form.auto_id  # Boolean or string
        if auto_id and "%s" in str(auto_id):
            return auto_id % self.html_name
        elif auto_id:
            return self.html_name
        return ""